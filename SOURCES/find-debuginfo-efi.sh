#!/bin/bash
#
# find-debuginfo-efi.sh
# Copyright 2017 Peter Jones <pjones@redhat.com>
#
# Distributed under terms of the GPLv3 license.
#

# trillian:~/build/BUILDROOT/fwupdate-8-5.fc27.x86_64$ ls -l usr/lib/debug/.build-id/fe/2390c7807b312e5fd9789af339b09a8317da96 usr/lib/debug/.build-id/fe/2390c7807b312e5fd9789af339b09a8317da96.debug usr/lib/debug/boot/efi/EFI/fedora/fwupx64.efi.debug
# lrwxrwxrwx. 1 pjones pjones   46 Jul 26 16:57 usr/lib/debug/.build-id/fe/2390c7807b312e5fd9789af339b09a8317da96 -> ../../../../../boot/efi/EFI/fedora/fwupx64.efi
# lrwxrwxrwx. 1 pjones pjones   43 Jul 26 16:57 usr/lib/debug/.build-id/fe/2390c7807b312e5fd9789af339b09a8317da96.debug -> ../../boot/efi/EFI/fedora/fwupx64.efi.debug
# -rwxr-xr-x. 1 pjones pjones 2.2M Jul 26 16:57 usr/lib/debug/boot/efi/EFI/fedora/fwupx64.efi.debug

set -u
set -e

for x in ${RPM_BUILD_ROOT}/usr/lib/debug/.build-id/*/* \
         $(find "${RPM_BUILD_ROOT}/usr/lib/debug" -iname '*.efi.debug')
do
    link=$(readlink "${x}") || :
    dn=$(dirname "${x}")
    if [[ ${link} =~ .*/fwup[[:alnum:]]+\.efi(\.debug)*$ ]] || \
       [[ ${x} =~ .*/fwup[[:alnum:]]+\.efi(\.debug)*$ ]] ; then
        echo "%dir ${dn}" | sed "s,${RPM_BUILD_ROOT},,g"
        echo "${x}" | sed "s,${RPM_BUILD_ROOT},,g"
    fi
done | sort | uniq >> debugfiles-efi.list

# vim:fenc=utf-8:tw=75
