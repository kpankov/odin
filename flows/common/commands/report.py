"""Reporter

Based on https://python.plainenglish.io/authenticating-jira-rest-api-in-python-and-creating-issues-oauth-4780c58fd478
"""
import datetime
import logging
import os
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
from jira import JIRA
from atlassian import Confluence

logger = logging.getLogger(__name__)

_command = {'help': "Reporter",
            'params': [{'name': 'out_dir', 'help': 'Output directory', 'default': None},
                       {'name': 'time_delta', 'help': 'Time delta (days)', 'default': None},
                       {'name': 'mail_list', 'help': 'Custom mailing list (separated by comma)', 'default': 'all'}],
            'flags': [{'name': 'pdf', 'help': 'Generate .pdf file.'},
                      {'name': 'mail', 'help': 'Send report by email (+pdf if possible). Only to managers if -min. '},
                      {'name': 'cnfl', 'help': 'Send report to confluence'}]}


def get_jira_qcs(core):
    jira_options = {'server': 'https://jira.quantenna.com'}

    return JIRA(options=jira_options,
                basic_auth=(core.project.get_var('JIRA_QCS_USER'), core.project.get_var('JIRA_QCS_PASS')))


def get_jira_onsemi(core):
    jira_options = {'server': 'https://jira.onsemi.com'}

    return JIRA(options=jira_options, token_auth=core.project.get_var('JIRA_ONSEMI_TOKEN'))


def get_issues(core, user_name_qcs, user_name_onsemi):
    issues_list_qcs = get_jira_qcs(core).search_issues(
        'assignee = {} or reporter = {}'.format(user_name_qcs, user_name_qcs),
        expand='changelog,comments',
        maxResults=1000)
    issues_list_onsemi = get_jira_onsemi(core).search_issues(
        'assignee = {} or reporter = {}'.format(user_name_onsemi, user_name_onsemi),
        expand='changelog,comments',
        maxResults=1000)

    logger.debug("{} issues fetched for {} (qcs).".format(issues_list_qcs.total, user_name_qcs))
    logger.debug("{} issues fetched for {} (onsemi).".format(issues_list_onsemi.total, user_name_onsemi))

    return issues_list_qcs, issues_list_onsemi


def sort_issues(core, issues_qcs, issues_onsemi, first_keys, time_delta):
    sorted_issues = {}
    sorted_issues_summary = {}

    final_statuses = ['Closed', 'Done', 'Resolved', 'Verified']
    new_onhold_statuses = ['New', 'On Hold', 'Unconfirmed', 'To Do', 'Open']

    for issue in issues_qcs + issues_onsemi:
        found = False
        summary = True
        actual_keys = []
        for key in first_keys:
            if key in issue.get_field('labels'):
                found = True
                actual_keys.append(key)

        # Check date of "close"
        if str(issue.get_field('status')) in final_statuses:
            for change in issue.changelog.histories:
                for change_item in change.items:
                    if change_item.field == 'status':
                        last_date = change.created

            last_date = last_date[:-2] + ":" + last_date[-2:]
            last_date = datetime.datetime.fromisoformat(last_date)
            utc = pytz.UTC
            last_date = last_date.replace(tzinfo=utc)
            if last_date < (datetime.datetime.today().replace(tzinfo=utc) - time_delta):  # time_delta days from today
                logger.debug('Issue {} - {} (closed {}) - Too old'.format(str(issue), issue.get_field('status'), last_date))
                continue
            else:
                logger.debug('Issue {} - {} (closed {})'.format(str(issue), issue.get_field('status'), last_date))
        else:
            if str(issue.get_field('status')) in new_onhold_statuses:
                summary = False

        if issue in issues_qcs:
            comments = get_jira_qcs(core).comments(issue)
            server = 'https://jira.quantenna.com'
        else:
            if issue in issues_onsemi:
                comments = get_jira_onsemi(core).comments(issue)
                server = 'https://jira.onsemi.com'
            else:
                logger.error("Undefined issue {} found!".format(str(issue)))
                server = ''

        # for comment in comments:
        #     print("Comment text : ", comment.body)
        #     print("Comment author : ", comment.author.displayName)
        #     print("Comment time : ", comment.created)

        if len(comments):
            issue_comment = comments[-1].body
            issue_comment = re.sub(r'^[\s]?#\s', '&#8226; ', issue_comment, flags=re.MULTILINE)
            # issue_comment = re.sub(r'\n#\s', '\n&#8226; ', issue_comment, flags=re.MULTILINE)  # TODO
            issue_comment = issue_comment.replace('\r\n', '\n').replace('\n\n', '\n').replace('\n', ' <br>')
            issue_comment = re.sub(
                r'\[(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)\]', r'\1',
                issue_comment, flags=re.MULTILINE)
        else:
            issue_comment = 'No comments'

        issue_fields = {
            'id': str(issue),
            'server': server,
            'type': issue.get_field('issuetype'),
            'summary': issue.get_field('summary'),
            # 'created': issue.get_field('created'),
            'status': str(issue.get_field('status')),
            'description': issue.get_field('description'),
            'resolution': str(issue.get_field('resolution')),
            'assignee': str(issue.get_field('assignee')),
            'reporter': str(issue.get_field('reporter')),
            'comment': issue_comment
        }

        if found is False:
            actual_keys = ['Other']

        for key in actual_keys:
            if sorted_issues.get(key) is None:
                sorted_issues[key] = [issue_fields]
            else:
                sorted_issues[key].append(issue_fields)
            if summary:
                if sorted_issues_summary.get(key) is None:
                    sorted_issues_summary[key] = [issue_fields]
                else:
                    sorted_issues_summary[key].append(issue_fields)

    return sorted_issues, sorted_issues_summary


def generate_files(core, team_report_header, team_list, team_labels, report_time_delta, markdown_file_path, html_file_path, mail_file_path, full=True):
    bootstrap_css_file_path = os.path.join(
        os.path.join(os.path.join(os.path.join(core.glob_vars["ODIN_PATH"], "flows"), "common"), "templates"),
        "bootstrap.min.css")

    # Open files
    markdown_file = open(markdown_file_path, 'w', encoding='UTF-8')
    html = open(html_file_path, 'w', encoding='UTF-8')
    html_mail = open(mail_file_path, 'w', encoding='UTF-8')

    # Write content
    markdown_file.write('# {}\n\n'.format(team_report_header))

    html.write('<!doctype html>\n<html lang="en">\n<head>\n')
    html.write('<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n')
    html.write('<title>{}</title>\n'.format(team_report_header))
    with open(bootstrap_css_file_path, 'r') as css_file:
        html.write('<style>')
        html.write(css_file.read())
        html.write('</style>\n')
    html.write('</head>\n<body class="px-3">\n')
    html.write('<h1 class="text-center">{}</h1>\n'.format(team_report_header))

    html_mail.write('<h1>{}</h1>\n'.format(team_report_header))

    first_person_flag = True
    for person in team_list:
        markdown_file.write('## {}\n\n'.format(person[0]))

        # Person's name
        if first_person_flag:
            html.write('<h2>{}</h2>\n'.format(person[0]))
            first_person_flag = False
        else:
            html.write('<h2 class="new-page">{}</h2>\n'.format(person[0]))
        html_mail.write('<h2>{}</h2>\n'.format(person[0]))

        # Table start
        html.write('<table class="table table-sm table-bordered">\n')
        html_mail.write('<table style="border: 1px solid gray; border-collapse: collapse;">\n')

        issues_qcs, issues_onsemi = get_issues(core, person[1], person[2])  # (QCS, Onsemi)
        sorted_issues, sorted_issues_summary = sort_issues(core, issues_qcs, issues_onsemi, team_labels, report_time_delta)
        if not full:
            sorted_issues = sorted_issues_summary

        # Table headers
        markdown_file.write('| Project | Issue&nbsp;ID | Status | Summary | Last&nbsp;comment |\n')
        markdown_file.write('| :-----: | :------: | :----: | :------ | :----------- |\n')

        html.write('\t<thead>\n\t\t<tr>\n')
        html.write('\t\t\t'
                   '<th>Project</th>'
                   '<th class="text-center">Issue&nbsp;ID</th>'
                   '<th class="text-center">Status</th>'
                   '<th>Summary</th>'
                   '<th>Last&nbsp;comment</th>'
                   '\n')
        html.write('\t\t</tr>\n\t</thead>\n')
        html.write('\t<tbody>\n')

        TH_STYLE = 'border: 1px solid gray; padding: 0.5em; background-color: #ebebeb; '
        html_mail.write('\t<tr>\n')
        html_mail.write('\t\t'
                        '<th style="' + TH_STYLE + '">Project</th>'
                        '<th style="' + TH_STYLE + 'text-align: center;">Issue&nbsp;ID</th>'
                        '<th style="' + TH_STYLE + 'text-align: center;">Status</th>'
                        '<th style="' + TH_STYLE + '">Summary</th>'
                        '<th style="' + TH_STYLE + '">Last&nbsp;comment</th>'
                        '\n')
        html_mail.write('\t</tr>\n')

        # Issues
        TD_STYLE = 'border: 1px solid gray; padding: 0.3em; '
        for project_label in team_labels:
            if sorted_issues.get(project_label) is None:
                continue
            first_issue_in_project = True
            for issue in sorted_issues[project_label]:
                html.write('\t\t<tr>\n')
                html_mail.write('\t<tr>\n')

                if first_issue_in_project:
                    markdown_file.write('| {}'.format(project_label))
                    html.write('\t\t\t<td')
                    html_mail.write('\t\t<td style="' + TD_STYLE + '"')
                    if len(sorted_issues[project_label]) > 1:
                        html.write(' rowspan="{}"'.format(len(sorted_issues[project_label])))
                        html_mail.write(' rowspan="{}"'.format(len(sorted_issues[project_label])))
                    html.write('><b>{}</b></td>\n'.format(project_label))
                    html_mail.write('><b>{}</b></td>\n'.format(project_label))
                    first_issue_in_project = False
                else:
                    markdown_file.write('| ')

                markdown_file.write('| [{}]({}/browse/{}) '.format(issue['id'], issue['server'], issue['id']))
                html.write('\t\t\t<td class="text-center">')
                html_mail.write('\t\t<td style="' + TD_STYLE + 'text-align: center;">')
                if str(issue['type']) == 'New Feature':
                    html.write('🚲')
                    html_mail.write('🚲')
                if str(issue['type']) == 'Task' or str(issue['type']) == 'Sub-task':
                    html.write('✔')
                    html_mail.write('✔')
                if str(issue['type']) == 'Improvement':
                    html.write('🚀')
                    html_mail.write('🚀')
                if str(issue['type']) == 'Epic':
                    html.write('⚡')
                    html_mail.write('⚡')
                if str(issue['type']) == 'Bug':
                    html.write('🐞')
                    html_mail.write('🐞')
                html.write('&nbsp;<a href="{}/browse/{}">{}</a>&nbsp;'.format(issue['server'], issue['id'], issue['id'].replace('-', '&#8209;')))
                html_mail.write('&nbsp;<a href="{}/browse/{}">{}</a>&nbsp;'.format(issue['server'], issue['id'], issue['id'].replace('-', '&#8209;')))
                name = ' '.join(person[0].split()[:2])
                if str(issue['reporter']) == name:
                    html.write('⬆')
                    html_mail.write('⬆')
                if str(issue['assignee']) == name:
                    html.write('⬇')
                    html_mail.write('⬇')
                html.write('</td>\n')
                html_mail.write('</td>\n')

                markdown_file.write('| {} '.format(issue['status']))

                badge = 'info'
                color = 'color:#fff; background-color:#17a2b8; '
                if issue['status'] in ['New', 'Open', 'To Do']:
                    badge = 'primary'
                    color = 'color:#fff; background-color:#007bff; '
                if issue['status'] in ['Assigned', 'In Progress']:
                    badge = 'warning'
                    color = 'color:#212529; background-color:#ffc107; '
                if issue['status'] in ['Closed', 'Done', 'Resolved', 'Verified']:
                    badge = 'success'
                    color = 'color:#fff; background-color:#28a745; '
                if issue['status'] in ['On Hold']:
                    badge = 'dark'
                    color = 'color:#fff; background-color:#343a40; '
                html.write('\t\t\t<td class="text-center"><span class="badge badge-{}">{}</span></td>\n'.format(badge, issue['status'].replace(' ', '&nbsp;')))
                html_mail.write('\t\t'
                                '<td style="' + TD_STYLE + 'text-align: center;">'
                                '<span style="display:inline-block;padding:.4em 1em;font-size:75%;font-weight:700;line-height:1;text-align:center;white-space:nowrap;vertical-align:baseline;border-radius:10px; {}">&nbsp;{}&nbsp;</span>'
                                '</td>'
                                '\n'.format(color, issue['status'].replace(' ', '&nbsp;')))

                markdown_file.write('| {} '.format(issue['summary']))
                html.write('\t\t\t<td>{}</td>\n'.format(issue['summary']))
                html_mail.write('\t\t<td style="' + TD_STYLE + '">{}</td>\n'.format(issue['summary']))

                markdown_file.write('| {} '.format(re.sub(
                    r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
                    r'[&#60;link&#62;](\1)', issue['comment'], flags=re.MULTILINE)))
                html.write('\t\t\t<td>{}</td>\n'.format(re.sub(
                    r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
                    r'<a href="\1">&#60;link&#62;</a>', issue['comment'], flags=re.MULTILINE)))
                html_mail.write('\t\t<td style="' + TD_STYLE + '">{}</td>\n'.format(re.sub(
                    r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
                    r'<a href="\1">&#60;link&#62;</a>', issue['comment'], flags=re.MULTILINE)))

                markdown_file.write('|\n')
                html.write('\t\t</tr>\n')
                html_mail.write('\t</tr>\n')
        markdown_file.write('\n')

        html.write('\t</tbody>\n</table>\n')
        html_mail.write('\t</tbody>\n</table>\n')
    legend = '<h2 class="new-page">Legend</h2>' \
             '<ul><li>🚲 &mdash; New Feature</li>' \
             '<li>✔ &mdash; Task, Sub-task</li>' \
             '<li>🚀 &mdash; Improvement</li>' \
             '<li>⚡ &mdash; Epic</li>' \
             '<li>🐞 &mdash; Bug</li>' \
             '<li>⬆ &mdash; Reporter</li>' \
             '<li>⬇ &mdash; Assignee</li></ul>'
    html.write(legend)
    html_mail.write(legend)
    html.write('</body>\n</html>\n')

    # Close files
    markdown_file.close()
    html.close()
    html_mail.close()


def run(core):

    # Dates
    date_ww = datetime.date.today().isocalendar()[1]
    date_this_day = datetime.date.today().strftime('%d_%b_%Y')

    if core.args.time_delta is None:
        report_time_delta = datetime.timedelta(core.project.get_var('TIME_DELTA'))
    else:
        report_time_delta = datetime.timedelta(int(core.args.time_delta))

    # Team
    team_name = core.project.get_var('TEAM_NAME')

    team_list = core.project.get_var('TEAM')
    team_labels = core.project.get_var('LABELS')

    # Files
    report_file_name_wo_ext = 'Report_{}_WW{}_{}'.format(team_name, date_ww, date_this_day)

    if core.args.out_dir is None:
        output_directory = os.path.abspath(os.path.curdir)
    else:
        output_directory = os.path.abspath(os.path.expanduser(core.args.out_dir))
        print("Output dir (from argument): {}".format(output_directory))
        if not os.path.isdir(output_directory):
            logger.error('Wrong path "{}"!'.format(output_directory))
            os.abort()

    # Full reports
    report_file_path_md = os.path.join(output_directory, report_file_name_wo_ext + '.md')
    report_file_path_html = os.path.join(output_directory, report_file_name_wo_ext + '.html')
    report_file_path_html_mail = os.path.join(output_directory, report_file_name_wo_ext + '_mail.html')
    report_file_path_pdf = os.path.join(output_directory, report_file_name_wo_ext + '.pdf')

    # Summary reports
    report_file_path_md_summary = os.path.join(output_directory, report_file_name_wo_ext + '_summary.md')
    report_file_path_html_summary = os.path.join(output_directory, report_file_name_wo_ext + '_summary.html')
    report_file_path_html_mail_summary = os.path.join(output_directory, report_file_name_wo_ext + '_mail_summary.html')
    report_file_path_pdf_summary = os.path.join(output_directory, report_file_name_wo_ext + '_summary.pdf')

    team_report_header = '{} Team Report WW{} ({})'.format(team_name, date_ww, date_this_day.replace('_', ' '))

    # Markdown & HTML
    logger.info('Generating Markdown&HTML ({}, {})...'.format(report_file_path_md, report_file_path_html))

    generate_files(core, team_report_header, team_list, team_labels, report_time_delta, report_file_path_md, report_file_path_html, report_file_path_html_mail)
    generate_files(core, team_report_header + ' Summary', team_list, team_labels, report_time_delta, report_file_path_md_summary, report_file_path_html_summary, report_file_path_html_mail_summary, full=False)

    # PDF
    if core.args.pdf:
        import pdfkit
        import socket

        if socket.gethostname().startswith('usca'):
            etx_flag = True

        pdfkit_config = pdfkit.configuration(wkhtmltopdf='/home/zbnnmf/wkhtmlto/wkhtmltopdf')

        logger.info('Generating PDF ({})...'.format(report_file_path_pdf))
        with open(report_file_path_html, 'r', encoding='UTF-8') as f:
            pdfkit_options = {'orientation': 'Landscape', 'page-size': 'A3', 'print-media-type': ''}
            if etx_flag:
                pdfkit.from_string(f.read(), report_file_path_pdf, configuration=pdfkit_config, options=pdfkit_options)
            else:
                pdfkit.from_string(f.read(), report_file_path_pdf, options=pdfkit_options)

        logger.info('Generating PDF Summary ({})...'.format(report_file_path_pdf_summary))
        with open(report_file_path_html_summary, 'r', encoding='UTF-8') as f:
            pdfkit_options = {'orientation': 'Landscape', 'page-size': 'A4', 'print-media-type': ''}
            if etx_flag:
                pdfkit.from_string(f.read(), report_file_path_pdf_summary, configuration=pdfkit_config, options=pdfkit_options)
            else:
                pdfkit.from_string(f.read(), report_file_path_pdf_summary, options=pdfkit_options)

    # E-Mail
    if core.args.mail:
        sender_mail = "noreply@onsemi.com"
        # recipients = ["Satyajit.NagChowdhury@onsemi.com"]
        if core.args.mail_list == 'all':
            recipients = core.project.get_var('MAILING_LIST')
        else:
            recipients = core.args.mail_list.split(',')

        msg = MIMEMultipart('alternative')

        msg['Subject'] = team_report_header
        msg['From'] = sender_mail
        msg['To'] = ", ".join(recipients)

        with open(report_file_path_html_mail_summary, 'r', encoding='UTF-8') as f:
            msg.attach(MIMEText(f.read(), 'html'))

        # attachment_file_list = [report_file_path_md, report_file_path_md_summary, report_file_path_html, report_file_path_html_summary]
        attachment_file_list = [report_file_path_html, report_file_path_html_summary]
        if core.args.pdf:
            attachment_file_list.append(report_file_path_pdf)
            attachment_file_list.append(report_file_path_pdf_summary)

        for f in attachment_file_list:
            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=os.path.basename(f)
                )

            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
            msg.attach(part)

        smtp = smtplib.SMTP("localhost")
        if smtp is not None:
            smtp.sendmail(sender_mail, recipients, msg.as_string())
            smtp.quit()

        logger.info("Email was sent successfully.")

    if core.args.cnfl:
        print('Posting to confluence...')

        # confluence = Confluence(
        #     url='https://confluence.onsemi.com',
        #     username=core.project.get_var('CONFLUENCE_USER'),
        #     password=core.project.get_var('CONFLUENCE_TOKEN'),
        #     cloud=True)

        # Workaround
        confluence = Confluence(
            url=core.project.get_var('CONFLUENCE_URL'),
            username=core.project.get_var('CONFLUENCE_USER'),
            password=core.project.get_var('CONFLUENCE_PASS'))

        space = core.project.get_var('CONFLUENCE_SPACE')
        parent_name = core.project.get_var('CONFLUENCE_PARENT')
        parent_id = confluence.get_page_id(space, parent_name)
        print('Parent page name "{}", id "{}"'.format(parent_name, parent_id))
        title = team_report_header
        body_file = open(report_file_path_html_mail_summary, 'r')
        body = body_file.read().replace('<br>', '<br/>').replace('<tbody>', '').replace('</tbody>', '')
        body = body.replace(r'@@', '@')
        body = re.sub(r"<([a-zA-Z0-9.!#$%&’*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)>", "<a href=\"mailto:\\g<1>\">\\g<1></a>", body, 0, re.MULTILINE)
        body = re.sub(r'&(?![#\w]+;)', '&amp;', body)
        if confluence.page_exists(space, title):
            content_id = confluence.get_page_id(space, title)
            print(content_id)
            print('Page exists, content_id "{}"'.format(content_id))
            # confluence.remove_content(content_id)
            # confluence.update_page(page_id, title, body, parent_id=None, type='page', representation='storage',
            #                        minor_edit=False)
            confluence.update_or_create(parent_id, title, body, representation='storage')
        else:
            confluence.create_page(space, title, body, parent_id=parent_id, type='page', representation='storage',
                                   editor='v2')

