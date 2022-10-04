# Std
import datetime
import logging
import pathlib
import yaml
import os

# Other
import pymongo

class BaseMongoDBExportBackend():
    def __init__(self, mongo_uri=None, database_name=None, debug_mode=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mongo_handler = None
        self.db_handler = None

        self.debug_mode = debug_mode

        self.database_name = database_name
        if (self.database_name is None):
            self.logger.critical(f"Database name is not specified")
            return

        if (mongo_uri is None):
            self.logger.critical(f"Mongo URI is not specified")
        else:
            try:
                self.mongo_handler = pymongo.MongoClient(mongo_uri)
                self.logger.info(f"Connection with {self.mongo_handler.address} host was established. "
                                 f"Database name: {self.database_name}")
                self.db_handler = self.mongo_handler[self.database_name]
            except Exception as e:
                self.logger.critical(f"Connection by the {mongo_uri} is not established due to error: {e}")
                self.mongo_handler = None

    # This method should be rewritten for particular realization
    def _particular_save_method(self, *args, **kwargs):
        return True

    def is_successfully_connected(self):
        return bool(self.mongo_handler)

    def save_data_to_db(self, *args, **kwargs):
        if (self.mongo_handler is None):
            self.logger.critical(f"Doesn't exist suitable mongo connection. Export operation is aborted.")
            return False

        return self._particular_save_method(*args, **kwargs)


class ScoreBoardAdaptBackend(BaseMongoDBExportBackend):

    def __init__(self, *args, **kwargs):
        super(ScoreBoardAdaptBackend, self).__init__(*args, **kwargs)
        self.releases_collection_name = 'validation_releases'
        self.builds_collection_name = 'validation_builds'
        self.sessions_collection_name = 'validation_sim_sessions'
        self.tests_collection_name = 'validation_sim_results'
        self.build_fields = ['strategy',
                             'iteration',
                             'path',
                             'result',
                             'chipscope',
                             'frequency',
                             'total_power',
                             'build_time',
                             'mode',
                             'type',
                             'avb_required',
                             'selected'
                            ]

    def __print_stat(self, error_cond, msg):
        if (error_cond):
            self.logger.error(msg)
        else:
            self.logger.info(msg)

    def __generate_adapt_test_structure(self, sim_test, session_id):
        adapt_test_result = {'session_id' : session_id,
                             'settings' : {'short' : {'test_name' : sim_test.get('name'),
                                                      'target' : sim_test.get('target')}},
                             'parsed' : {'status' : sim_test.get('result')}}
        return adapt_test_result

    def _particular_save_method(self, release, builds, sim_tests, user, date):

        selected_builds = {}

        release_collection = self.db_handler[self.releases_collection_name]
        builds_collection = self.db_handler[self.builds_collection_name]
        sessions_collection = self.db_handler[self.sessions_collection_name]
        tests_collection = self.db_handler[self.tests_collection_name]

        sessions = {}

        # uploading data
        release['user'] = user # adding user field to release before saving to DB
        release_id = release_collection.insert_one(release).inserted_id
        if (release_id is not None):
            self.logger.info(f"Release id - {release_id}")

            for build in builds:
                build["release_id"] = release_id
                build['user'] = user
                build_id = builds_collection.insert_one(build).inserted_id
                if (build_id is not None):
                    build["build_id"] = build_id

                    target = build.get('target')
                    selected = build.get('selected', False)

                    if (target is not None and selected):
                        if (selected_builds.get(target) is None):
                            selected_builds[target] = build_id

                else:
                    self.logger.error(f"Can't upload build "
                                      f"({build.get('target')}, {build.get('strategy')}, "
                                      f"{build.get('iteration')}, {build.get('path')})"
                                      f"to ADAPT DB")

            for sim_group, sim_tests_list in sim_tests.items():

                session_id = sessions.get(sim_group, {}).get('session_id', None)
                if (session_id is None):
                    session = {'release_id' : release_id, 'name' : sim_group, 'type' : 'simulation', 'user' : user, 'date' : date}
                    sessions[sim_group] = {'release_id' : release_id, 'session_id' : None, 'tests': []}
                    session_id = sessions_collection.insert_one(session).inserted_id
                    if (session_id is not None):
                        sessions[sim_group]['session_id'] = session_id
                    else:
                        self.logger.error(f"Can't upload session data ({sim_group}) to ADAPT DB. "
                                          f"Skipping uploading {len(sim_tests_list)} tests.")
                        continue

                for sim_test in sim_tests_list:
                    sim_test['session_id'] = session_id
                    sim_test['user'] = user
                    sim_test_id = tests_collection.\
                        insert_one(self.__generate_adapt_test_structure(sim_test, session_id)).inserted_id
                    if (sim_test_id is not None):
                        sim_test['id'] = sim_test_id
                        sessions[sim_group]['tests'].append(sim_test)
                    else:
                        self.logger.error(f"Can't upload test ({sim_group}, {sim_test.get('name', None)}) "
                                          f"to ADAPT DB")
        else:
            self.logger.error(f"Can't upload Release instance ({release.get('name')}) to ADAPT DB")

        #calculating statistic
        releases_total = 1
        releases_saved = 0
        if (release_id):
            releases_saved = 1

        builds_total = len(builds)
        builds_saved = sum([build.get('build_id', None) is not None for build in builds])

        sessions_total = len(sim_tests.keys())
        sim_tests_total = sum([len(sim_tests_list) for sim_tests_list in sim_tests.values()])

        sessions_saved = 0
        sim_tests_saved = 0
        for session in sessions.values():
            if (session.get('session_id', None) is not None):
                sessions_saved += 1

            sim_tests_saved += sum([test.get('id', None) is not None for test in session.get('tests', [])])

        # printing statistic
        self.__print_stat(error_cond = releases_total != releases_saved,
                          msg = f"Saved {releases_saved} Releases from {releases_total} total")
        self.__print_stat(error_cond = builds_total != builds_saved,
                          msg=f"Saved {builds_saved} Builds from {builds_total} total")
        self.__print_stat(error_cond = sessions_total != sessions_saved,
                          msg=f"Saved {sessions_saved} Sessions from {sessions_total} total")
        self.__print_stat(error_cond = sim_tests_total != sim_tests_saved,
                          msg=f"Saved {sim_tests_saved} Tests from {sim_tests_total} total")

        # calculate final status
        status = releases_total == releases_saved and \
                 builds_total == builds_saved and \
                 sessions_total == sessions_saved and \
                 sim_tests_total == sim_tests_saved

        return {'status' : status,
                'release_id' : release_id,
                'selected_builds_id' : selected_builds}

    def __get_pathlib(self, filepath):
        if (not isinstance(filepath, pathlib.Path)):
            filepath = pathlib.Path(filepath)
        return filepath

    def __get_scoreboard(self, filepath):
        filepath = self.__get_pathlib(filepath)
        scoreboard = None
        with open(filepath, "rt") as stream:
            try:
                scoreboard = yaml.safe_load(stream)
            except Exception as e:
                scoreboard = None
                self.logger.info(f"Can't load scoreboard from {filepath} due to {e}")
        return scoreboard

    def __get_steps_list(self, scoreboard_steps):
        # get sorted list of steps
        plain_steps_list = sorted([{**b, 'name' : a} for a,b in scoreboard_steps.items()],
                            key=lambda step: step.get('step', 0))

        # delete excessive info
        for step in plain_steps_list:
            step.pop('step', None)

        return plain_steps_list

    def __create_release(self, scoreboard, name, comment, date):
        release_dict = {'name' : name,
                        'date' : date,
                        'chip' : scoreboard.get('project', {}),
                        'comment' : comment,
                        'repositories' : scoreboard.get('repositories', {}),
                        'steps' : self.__get_steps_list(scoreboard.get('steps', {}))}
        if (scoreboard.get('platform')):
            release_dict['platform'] = scoreboard.get('platform')

        return release_dict

    def __create_builds(self, scoreboard, release_date):

        plain_builds_list = []
        # cycle for all targets
        for target_platform, builds in scoreboard.get('builds', {}).items():
            # cycle for all build for particular target
            for build_idx, build in enumerate(builds):
                necessary_build_fields = self.build_fields.copy()
                plain_build = {}
                # cycle for all fields in particular build
                for field_name, value in build.items():
                    if (field_name in necessary_build_fields):
                        plain_build[field_name] = value
                        necessary_build_fields.remove(field_name)
                        continue
                    if (field_name.startswith("timing_")):
                        new_field_name = field_name.replace("timings_", "")
                        if (plain_build.get('timings', None) is None):
                            plain_build['timings'] = {}
                        plain_build['timings'][new_field_name] = value
                        continue

                plain_build['target'] = target_platform
                plain_build['date'] = release_date
                plain_builds_list.append(plain_build)

        return plain_builds_list

    def __create_sim_tests(self, scoreboard):

        scoreboard_sim_tests = scoreboard.get('sim_tests', {})
        sim_tests = {}
        for test_name, details in scoreboard_sim_tests.items():
            test_type = str(details.get('type', None))
            # processing tests only with valid type
            if (test_type != 'None'):
                # creating new storage for test type if doesn't exist
                if (not sim_tests.get(test_type, False)):
                        sim_tests[test_type] = []
                test = {'name' : test_name,
                        'result' : details.get('result', False),
                        'target' : details.get('target', [])}
                sim_tests[test_type].append(test)

        return sim_tests

    def upload_release_scoreboard(self, scoreboard_filepath, release_name,
                                  release_comment = str(),
                                  release_date = datetime.datetime.now(),
                                  user = os.environ.get('USER')):

        scoreboard = self.__get_scoreboard(scoreboard_filepath)
        release = self.__create_release(scoreboard, release_name, release_comment, release_date)
        builds = self.__create_builds(scoreboard, release_date)
        sim_tests = self.__create_sim_tests(scoreboard)
        results = self.save_data_to_db(release = release, builds = builds, sim_tests = sim_tests,
                                       user = user, date = release_date)

        return results

def test():

    import random
    r_num = random.randint(10000,99999)

    logging.basicConfig(  # filename=log_path.joinpath(log_file_name),
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%H:%M:%S")

    #data_uploader = ScoreBoardAdaptBackend(mongo_uri = "mongodb://localhost:27017",
    #                                       database_name = "ADAPT_123")
    data_uploader = ScoreBoardAdaptBackend(mongo_uri = "mongodb://adapt.quantenna.com:27020",
                                           database_name = "ADAPT_12345")
    result = data_uploader.upload_release_scoreboard(pathlib.Path("scoreboard.yaml"),
                                                     release_name = f"Test release #{r_num}",
                                                     release_comment = f"Test comment to release #{r_num}",
                                                     release_date = datetime.datetime.now(),
                                                     # user autodetection works well on Linux machines,
                                                     # on windows machines should be defined particular string user_name
                                                     user = os.environ.get('USER'))


    print(result)

if __name__ == '__main__':
    test()