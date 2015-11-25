#!/bin/bash
#
# Use this script to use interfaces/files from tempest-lib.
# Many files have been migrated to tempest-lib and tempest has
# its own copy too.
# This script helps to remove those from tempest and make use of tempest-lib.
# It adds the change-id of each file on which they were migrated in lib.
# This should only be done for files which were migrated to lib with
# "Migrated" in commit message as done by tempest-lib/tools/migrate_from_tempest.sh script.
# "Migrated" keyword is used to fetch the migration commit history from lib.
# To use:
#  1. Create a new branch in the tempest repo so not to destroy your current
#     working branch
#  2. Run the script from the repo dir and specify the file paths relative to
#     the root tempest dir(only code and unit tests):
#
#   tools/use_tempest_lib.sh.sh tempest/file1.py tempest/file2.py


function usage {
    echo "Usage: $0 [OPTION] file1 file2 .."
    echo "Use files from tempest-lib"
    echo -e "Input files should be tempest files with path. \n  Example- tempest/file1.py tempest/file2.py .."
    echo ""
    echo "-s, --service_client Specify if files are service clients."
    echo "-u, --tempest_lib_git_url Specify the repo to clone tempest-lib from."
}

function check_all_files_valid {
    failed=0
    for file in $files; do
        # Get the latest change-id for each file
        latest_commit_id=`git log -n1 -- $file | grep "^commit" | awk '{print $2}'`
        cd $tmpdir
        filename=`basename $file`
        lib_path=`find ./ -name $filename`
        if [ -z $lib_path ]; then
            echo "ERROR: $filename does not exist in tempest-lib."
            failed=$(( failed + 1))
            cd - > /dev/null
            continue
        fi
        # Get the CHANGE_ID of tempest-lib patch where file was migrated
        migration_change_id=`git log  -n1 --grep "Migrated" -- $lib_path | grep "Change-Id: " | awk '{print $2}'`
        MIGRATION_IDS=`echo -e "$MIGRATION_IDS\n * $filename: $migration_change_id"`
        # Get tempest CHANGE_ID of file which was migrated to lib
        migrated_change_id=`git log  -n1 --grep "Migrated" -- $lib_path | grep "* $filename"`
        migrated_change_id=${migrated_change_id#*:}
        cd - > /dev/null
        # Get the commit-id of tempest which was migrated to tempest-lib
        migrated_commit_id=`git log --grep "$migrated_change_id" -- $file | grep "^commit" | awk '{print $2}'`
        DIFF=$(git diff $latest_commit_id $migrated_commit_id $file)
        if [ "$DIFF" != "" ]; then
            echo "ERROR: $filename in tempest has been updated after migration to tempest-lib. First sync the file to tempest-lib."
            failed=$(( failed + 1))
        fi
    done
    if [[ $failed -gt 0 ]]; then
        echo "$failed files had issues"
        exit $failed
    fi
}

set -e

service_client=0
file_list=''

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit;;
        -u|--tempest_lib_git_url) tempest_lib_git_url="$2"; shift;;
        -s|--service_client) service_client=1;;
        *) files="$files $1";;
    esac
    shift
done

if [ -z "$files" ]; then
    usage; exit
fi

TEMPEST_LIB_GIT_URL=${tempest_lib_git_url:-git://git.openstack.org/openstack/tempest-lib}

tmpdir=$(mktemp -d -t use-tempest-lib.XXXX)

# Clone tempest-lib
git clone $TEMPEST_LIB_GIT_URL $tmpdir

# Checks all provided files are present in lib and
# not updated in tempest after migration to lib.
check_all_files_valid

for file in $files; do
    rm -f $file
    tempest_dir=`pwd`
    tempest_dir="$tempest_dir/tempest/"
    tempest_dirname=`dirname $file`
    lib_dirname=`echo $tempest_dirname | sed s@tempest\/@tempest_lib/\@`
    # Convert tempest dirname to import string
    tempest_import="${tempest_dirname//\//.}"
    tempest_import=${tempest_import:2:${#tempest_import}}
    if [ $service_client -eq 1 ]; then
        # Remove /json path because tempest-lib supports JSON only without XML
        lib_dirname=`echo $lib_dirname | sed s@\/json@@`
    fi
    # Convert tempest-lib dirname to import string
    tempest_lib_import="${lib_dirname//\//.}"
    tempest_lib_import=${tempest_lib_import:2:${#tempest_lib_import}}
    module_name=`basename $file .py`
    tempest_import1="from $tempest_import.$module_name"
    tempest_lib_import1="from $tempest_lib_import.$module_name"
    tempest_import2="from $tempest_import import $module_name"
    tempest_lib_import2="from $tempest_lib_import import $module_name"
    set +e
    grep -rl "$tempest_import1" $tempest_dir | xargs sed -i'' s/"$tempest_import1"/"$tempest_lib_import1"/g 2> /dev/null
    grep -rl "$tempest_import2" $tempest_dir | xargs sed -i'' s/"$tempest_import2"/"$tempest_lib_import2"/g 2> /dev/null
    set -e
    if [[ -z "$file_list" ]]; then
        file_list="$module_name"
    else
        tmp_file_list="$file_list, $module_name"
        char_size=`echo $tmp_file_list | wc -c`
        if [ $char_size -lt 27 ]; then
            file_list="$file_list, $module_name"
        fi
    fi
done

rm -rf $tmpdir
echo "Completed. Run pep8 and fix error if any"

git add -A tempest/
# Generate a migration commit
commit_message="Use $file_list from tempest-lib"
pre_list=$"The files below have been migrated to tempest-lib\n"
pre_list=`echo -e $pre_list`
post_list=$"Now Tempest-lib provides those as stable interfaces. So Tempest should\nstart using those from lib and remove its own copy."
post_list=`echo -e $post_list`

git commit -m "$commit_message" -m "$pre_list" -m "$MIGRATION_IDS" -m "$post_list"
