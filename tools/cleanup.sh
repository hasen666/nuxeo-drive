#!/bin/bash -eu
#
# Delete old alpha releases.
#
# Warning: do not execute this script manually but from Jenkins.
#

main() {
    local older_than
    local path
    local release
    local version

    older_than=21
    path="/var/www/community.nuxeo.com/static/drive-updates"

    echo ">>> Installing requirements"
    python -m pip install --user pyyaml==5.1.2

    echo ">>> Retrieving versions.yml"
    rsync -vz nuxeo@lethe.nuxeo.com:${path}/versions.yml .

    echo ">>> Checking versions.yml integrity"
    python tools/versions.py --check || exit 1

    echo ">>> Removing alpha versions older than ${older_than} days"
    while IFS= read release; do
        version="$(echo ${release} | sed s'/alpha-//')"
        echo " - ${version}"
        python tools/versions.py --delete "${version}"
    done < <(git tag -l "alpha-*" --sort=-taggerdate | tail -n +${older_than})

    echo ">>> Checking versions.yml integrity"
    python tools/versions.py --check || exit 1

    echo ">>> Uploading versions.yml"
    rsync -vz versions.yml nuxeo@lethe.nuxeo.com:${path}/

    echo ">>> Removing binaries, tags and branches:"
    while IFS= read release; do
        version="$(echo ${release} | sed s'/alpha-//')"
        echo " - ${version}"
        ssh -T nuxeo@lethe.nuxeo.com "rm -vf ${path}/alpha/*${version}.* ${path}/alpha/*${version}-*" || true
        git tag --delete "${release}" || true
        git push --delete origin "wip-${release}" || true  # branch
        git push --delete origin "${release}" || true  # tag
    done < <(git tag -l "alpha-*" --sort=-taggerdate | tail -n +${older_than})
}

main
