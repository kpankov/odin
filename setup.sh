#!/bin/bash

_my_command()
{
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    subcommands_1="completion set_project info graph check_tools create_sos_wa open_sos close_sos update fpga_filelist fpga_sim fpga_build fpga_release fpga_chipscope" #возможные подкоманды первого уровня
    #subcommands_history="import export"
    subcommands_set_project="--proj"
    subcommands_set_project_proj="emerald_fpga vivado_project"
    subcommands_fpga_sim="--PLATFORM --GUI"
    subcommands_fpga_sim_platform="2.1 3_c 3_d"
    subcommands_fpga_sim_gui="yes no"
    subcommands_fpga_build="--PLATFORM --LSF"
    subcommands_fpga_build_platform="2.1 3_c 3_d"
    subcommands_fpga_build_lsf="on off"
    subcommands_fpga_release="--BUILD_FOLDER_C --BUILD_FOLDER_D --VER --BUILD --PLATFORM --dryrun"
    subcommands_fpga_release_platform="2.1 3"
    subcommands_fpga_release_dryrun="0 1"
    subcommands_open_sos="--proj"
    subcommands_open_sos_proj="emerald qcs-mac qcs-hdp qcs-ip qcs-bb qcs-lib Ruby"
    
    
    if [[ ${COMP_CWORD} == 1 ]] ; then # цикл определения автодополнения при вводе подкоманды первого уровня
        COMPREPLY=( $(compgen -W "${subcommands_1}" -- ${cur}) )
        return 0
    fi
    
    
    subcmd_1="${COMP_WORDS[1]}" #К данному моменту подкоманда первого уровня уже введена, и мы её выбираем в эту переменную
    case "${subcmd_1}" in #Дальше смотри, что она из себя представляет
    open_sos)
        if [[ ${COMP_CWORD} == 2 ]] ; then
            COMPREPLY=( $(compgen -W "${subcommands_open_sos}" -- ${cur}) )
            return 0
        fi
        
        subcmd_2="${COMP_WORDS[2]}"

        if [[ ${COMP_CWORD} == 3 ]] ; then #но в любом случае следующим аргументом идет имя проекта.
            COMPREPLY=($(compgen -W "${subcommands_open_sos_proj}" -- ${cur}))
            return 0
        fi

        return 0
        ;;
    set_project)
        if [[ ${COMP_CWORD} == 2 ]] ; then
            COMPREPLY=( $(compgen -W "${subcommands_set_project}" -- ${cur}) )
            return 0
        fi
        
        subcmd_2="${COMP_WORDS[2]}"

        if [[ ${COMP_CWORD} == 3 ]] ; then #но в любом случае следующим аргументом идет имя проекта.
            COMPREPLY=($(compgen -W "${subcommands_set_project_proj}" -- ${cur}))
            return 0
        fi

        return 0
        ;;
    fpga_sim)
        if [[ ${COMP_CWORD} == 2 ]] ; then
            COMPREPLY=( $(compgen -W "${subcommands_fpga_sim}" -- ${cur}) )
            return 0
        fi
        
        subcmd_2="${COMP_WORDS[2]}"

        # if [[ ${COMP_CWORD} == 3 ]] ; then #но в любом случае следующим аргументом идет имя проекта.
        #     COMPREPLY=($(compgen -W "${subcommands_fpga_sim_platform}" -- ${cur}))
        #     return 0
        # fi

        case "${subcmd_2}" in
        --PLATFORM)
            COMPREPLY=($(compgen -W "${subcommands_fpga_sim_platform}" -- ${cur}))
            return 0
            ;;
        --GUI)
            COMPREPLY=($(compgen -W "${subcommands_fpga_sim_gui}" -- ${cur}))
            return 0
            ;;
        esac

        return 0
        ;;
    fpga_build)
        if [[ ${COMP_CWORD} == 2 ]] ; then
            COMPREPLY=( $(compgen -W "${subcommands_fpga_build}" -- ${cur}) )
            return 0
        fi
        
        subcmd_2="${COMP_WORDS[2]}"

        case "${subcmd_2}" in
        --PLATFORM)
            COMPREPLY=($(compgen -W "${subcommands_fpga_build_platform}" -- ${cur}))
            return 0
            ;;
        --LSF)
            COMPREPLY=($(compgen -W "${subcommands_fpga_build_lsf}" -- ${cur}))
            return 0
            ;;
        esac

        return 0
        ;;
    fpga_release)
        if [[ ${COMP_CWORD} == 2 ]] ; then
            COMPREPLY=( $(compgen -W "${subcommands_fpga_release}" -- ${cur}) )
            return 0
        fi
        
        subcmd_2="${COMP_WORDS[2]}"

        case "${subcmd_2}" in
        --PLATFORM)
            COMPREPLY=($(compgen -W "${subcommands_fpga_release_platform}" -- ${cur}))
            return 0
            ;;
        --dryrun)
            COMPREPLY=($(compgen -W "${subcommands_fpga_release_dryrun}" -- ${cur}))
            return 0
            ;;
        esac

        return 0
        ;;
#    history)
#
#        if [[ ${COMP_CWORD} == 2 ]] ; then #введены script history; надо подставить import или export
#            COMPREPLY=( $(compgen -W "${subcommands_history}" -- ${cur}) )
#            return 0
#        fi
#
#        #к данному моменту мы уже знаем, что делаем: импорт или экспорт
#        subcmd_2="${COMP_WORDS[2]}"
#
#        if [[ ${COMP_CWORD} == 3 ]] ; then #но в любом случае следующим аргументом идет имя проекта.
#            COMPREPLY=($(compgen -W "`ls ${HOME}/projects`" -- ${cur}))
#            return 0
#        fi
#
#        case "${subcmd_2}" in #а дальше у импорта и экспорта набор флагов разный. мы смотрим на предпоследний аргумент, и если он является флагом - подставляем соответствующие ему значения, иначе - выдаем на дополнение список флагов.
#        import)
#            case "${COMP_WORDS[COMP_CWORD-1]}" in
#            -src) 
#                COMPREPLY=($(compgen -d -- ${cur})) #тут должна быть директория с исходниками
#                return 0
#                ;;
#            -file)
#                COMPREPLY=($(compgen -f -- ${cur})) #тут должен быть импортируемый файл
#                return 0
#                ;;
#            *)
#                COMPREPLY=($(compgen -W "-src -file" -- ${cur})) #список возможных флагов
#                return 0
#                ;;
#            esac
#            ;;
#
#        export) #у экспорта только один флаг -o, если был он - то мы предлагаем дополнение до файла, куда экспортировать, иначе - предлагаем дополнение до флага
#            if [[ ${COMP_WORDS[COMP_CWORD-1]} == "-o" ]] ; then 
#                COMPREPLY=($(compgen -f -- ${cur}))
#                return 0
#            fi
#            
#            COMPREPLY=($(compgen -W "-o" -- ${cur}))
#            return 0
#            ;;
#        *)
#            ;;
#        esac
#        ;;
#    help) #список возможных дополнений после help совпадает со списком подкоманд первого уровня, их и исследуем.
#	COMPREPLY=( $(compgen -W "${subcommands_1}" -- ${cur}))
#	return 0
#        ;;
    esac
    return 0
    
}

alias odin.py="python3 $(pwd)/odin.py"
complete -F _my_command odin.py
#export PROJECT_XML=$(pwd)/flows/common/projects/sample_xml/project.xml
#export PROJECT_YAML=$(pwd)/flows/common/projects/sample_yaml/project.yaml
