%global efivar_version 35-1
%global efibootmgr_version 16-1
%global gnu_efi_version 3.0.8-1
%undefine _debuginfo_subpackages

Name:           fwupdate
Version:        11
Release:        3%{?dist}
Summary:        Tools to manage UEFI firmware updates
License:        GPLv2+
URL:            https://github.com/rhinstaller/fwupdate
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
BuildRequires:  efivar-devel >= %{efivar_version}
BuildRequires:  gnu-efi >= %{gnu_efi_version}
BuildRequires:  gnu-efi-devel >= %{gnu_efi_version}
BuildRequires:  pesign
BuildRequires:  elfutils popt-devel git gettext pkgconfig
BuildRequires:  systemd
BuildRequires:  libabigail
%ifarch x86_64
BuildRequires: libsmbios-devel
%endif
ExclusiveArch:  x86_64 aarch64
Source0:        https://github.com/rhinstaller/fwupdate/releases/download/%{name}-%{version}/%{name}-%{version}.tar.bz2
Source1:        find-debuginfo-efi.sh
Source2:        securebootca.cer
Source3:        secureboot.cer

Patch0001: Fix-dependency-chain-for-a-parallel-make-issue.patch

%global __os_install_post %{expand:\
  %{?__debug_package:%{__debug_install_post}} \
  %{SOURCE1} \
  %{__arch_install_post} \
  %{__os_install_post} \
  %{nil}}%{nil}

%ifarch x86_64
%global efiarch x64
%global efialtarch ia32
%endif
%ifarch aarch64
%global efiarch aa64
%endif

# Figure out the right file path to use
%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))

%description
fwupdate provides a simple command line interface to the UEFI firmware updates.

%package libs
Summary: Library to manage UEFI firmware updates
%ifnarch %{ix86}
Requires: shim
%endif
Requires: %{name}-efi = %{version}-%{release}

%description libs
Library to allow for the simple manipulation of UEFI firmware updates.

%package devel
Summary: Development headers for libfwup
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: efivar-devel >= %{efivar_version}

%description devel
development headers required to use libfwup.

%package efi
Summary: UEFI binaries used by libfwup
Requires: %{name}-libs = %{version}-%{release}

%description efi
UEFI binaries used by libfwup.

%package efi-debuginfo
Summary: debuginfo for UEFI binaries used by libfwup
Requires: %{name}-efi = %{version}-%{release}
AutoReq: 0
AutoProv: 1

%description efi-debuginfo
debuginfo for UEFI binaries used by libfwup.

%prep
%setup -q -n %{name}-%{version}
git init
git config user.email "%{name}-owner@fedoraproject.org"
git config user.name "Fedora Ninjas"
git add .
mkdir build-%{efiarch}
%ifarch x86_64
mkdir build-%{efialtarch}
%endif
git commit -a -q -m "%{version} baseline."
git am %{patches} </dev/null
git config --unset user.email
git config --unset user.name
git config fwupdate.efidir %{efidir}

%build
cd build-%{efiarch}
make TOPDIR=.. -f ../Makefile OPT_FLAGS="$RPM_OPT_FLAGS" \
     libdir=%{_libdir} bindir=%{_bindir} \
     EFIDIR=%{efidir} %{?_smp_mflags}
mv -v efi/fwup%{efiarch}.efi efi/fwup%{efiarch}.unsigned.efi
%pesign -s -i efi/fwup%{efiarch}.unsigned.efi -o efi/fwup%{efiarch}.efi -a %{SOURCE2} -n redhatsecureboot301 -c %{SOURCE3}
cd ..

%ifarch x86_64
cd build-%{efialtarch}
setarch linux32 -B make TOPDIR=.. -f ../Makefile ARCH=%{efialtarch} \
                        OPT_FLAGS="$RPM_OPT_FLAGS" \
                        libdir=%{_libdir} bindir=%{_bindir} \
                        EFIDIR=%{efidir} %{?_smp_mflags}
mv -v efi/fwup%{efialtarch}.efi efi/fwup%{efialtarch}.unsigned.efi
%pesign -s -i efi/fwup%{efialtarch}.unsigned.efi -o efi/fwup%{efialtarch}.efi -a %{SOURCE2} -n redhatsecureboot301 -c %{SOURCE3}
cd ..
%endif

%install
rm -rf $RPM_BUILD_ROOT
cd build-%{efiarch}
%make_install TOPDIR=.. -f ../Makefile \
              EFIDIR=%{efidir} RPMARCH=%{_arch} RELEASE=%{RELEASE} \
              libdir=%{_libdir} bindir=%{_bindir} mandir=%{_mandir} \
              localedir=%{_datadir}/locale/ includedir=%{_includedir} \
              libexecdir=%{_libexecdir} datadir=%{_datadir} \
              sharedstatedir=%{_sharedstatedir}
cd ..

%ifarch x86_64
cd build-%{efialtarch}
setarch linux32 -B %make_install ARCH=%{efialtarch} TOPDIR=.. -f ../Makefile \
                                 EFIDIR=%{efidir} RPMARCH=%{_arch} \
                                 RELEASE=%{RELEASE} libdir=%{_libdir} \
                                 bindir=%{_bindir} mandir=%{_mandir} \
                                 localedir=%{_datadir}/locale/ \
                                 includedir=%{_includedir} \
                                 libexecdir=%{_libexecdir} \
                                 datadir=%{_datadir} \
                                 sharedstatedir=%{_sharedstatedir}
cd ..
%endif

%post libs
/sbin/ldconfig
%systemd_post fwupdate-cleanup.service

%preun libs
%systemd_preun fwupdate-cleanup.service

%postun libs
/sbin/ldconfig
%systemd_postun_with_restart pesign.service

%check
%ifarch x86_64
make abicheck
%endif

%files
%defattr(-,root,root,-)
%{!?_licensedir:%global license %%doc}
%license COPYING
# %%doc README
%{_bindir}/fwupdate
%{_datadir}/locale/en/fwupdate.po
%doc %{_mandir}/man1/*
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/fwupdate

%files devel
%defattr(-,root,root,-)
%doc %{_mandir}/man3/*
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc

%files libs
%defattr(-,root,root,-)
%{_libdir}/*.so.*
%{_datadir}/locale/en/libfwup.po
%{_unitdir}/fwupdate-cleanup.service
%attr(0755,root,root) %dir %{_sharedstatedir}/fwupdate/
%config(noreplace) %ghost %{_sharedstatedir}/fwupdate/done
%attr(0755,root,root) %dir %{_libexecdir}/fwupdate/
%{_libexecdir}/fwupdate/cleanup

%files efi
%dir %attr(0700,root,root) /boot/efi
%dir %attr(0700,root,root) /boot/efi/EFI/%{efidir}/
%dir %attr(0700,root,root) /boot/efi/EFI/%{efidir}/fw/
%attr (0700,root,root) /boot/efi/EFI/%{efidir}/fwup%{efiarch}.efi
%ifarch x86_64
%attr (0700,root,root) /boot/efi/EFI/%{efidir}/fwup%{efialtarch}.efi
%endif

%files efi-debuginfo -f debugfiles-efi.list
%defattr(-,root,root)

%changelog
* Thu Feb 21 2019 Javier Martinez Canillas <javierm@redhat.com> 11-3
- Fix dependency chain issue when doing a parallel make
  Related: rhbz#1677579

* Thu Feb 21 2019 Peter Jones <pjones@redhat.com> 11-3
- Fix secure boot signing for RHEL 8
  Resolves: rhbz#1677579

* Thu Feb 21 2019 Javier Martinez Canillas <javierm@redhat.com> 11-2
- Rebuild for signing with the proper key.
  Resolves: rhbz#1677579

* Mon Apr 09 2018 Peter Jones <pjones@redhat.com> - 11-1
- Update to fwupdate 11

* Thu Mar 01 2018 Peter Jones <pjones@redhat.com> - 10-6
- Fix fwup.pc

* Tue Feb 27 2018 Peter Jones <pjones@redhat.com> - 10-5
- Rebuild because I forgot to make sure efivar-34 was already in the
  buildroot.

* Tue Feb 27 2018 Peter Jones <pjones@redhat.com> - 10-4
- Roll in some bugfixes that'll be in fwupdate-11 upstream.
  This helps fix a couple of vendors machines.

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Jan 18 2018 Peter Jones <pjones@redhat.com> - 10-2
- Make really sure everything in /boot/efi is 0700 so we don't conflict with
  the grub packages.

* Mon Jan 08 2018 Peter Jones <pjones@redhat.com> - 10-1
- Update to the final released version 10.
- Make everything under /boot/efi be mode 0700, since that's what FAT will
  show anyway.

* Tue Sep 12 2017 Peter Jones <pjones@redhat.com> - 10-0.2
- Update for version 10
- test release for ux capsule support; to enable UX capsules define
  LIBFWUP_ADD_UX_CAPSULE=1 in your environment.

* Thu Aug 24 2017 Peter Jones <pjones@redhat.com> - 9-0.2
- Rebuild for aarch64 .reloc fix.

* Tue Aug 22 2017 Peter Jones <pjones@redhat.com> - 9-0.1
- Update to fwupdate 9
- Support ia32

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 8-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Peter Jones <pjones@redhat.com> - 8-6
- Try to make debuginfo generation work with rpm-4.13.0.1-38.fc27.x86_64

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 8-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Jul 08 2017 Peter Jones <pjones@redhat.com> - 8-4
- Rebuild for efivar-31-1.fc26
  Related: rhbz#1468841
- Fix some gcc 7 quirks

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Sep 27 2016 Peter Jones <pjones@redhat.com> - 8-2
- Rebuild for efivar 30.

* Fri Aug 19 2016 Peter Jones <pjones@redhat.com> - 8-1
- Update to fwupdate 8
- Fix some i686 build errors
- Be less stupid about SONAMEs so in the future we'll only have to rebuild
  dependent things on actual ABI changes.
- Only depend on libsmbios on x86, for now, because it hasn't been ported to
  Aarch64.

* Wed Aug 17 2016 Peter Jones <pjones@redhat.com> - 7-1
- Update to fwupdate 7
- Fix the fix for ae7b85
- fix one place where a second "rc" varibale is clobbering a result.

* Tue Aug 16 2016 Peter Jones <pjones@redhat.com> - 6-1
- Update to fwupdate 6
- lots of build fixes for newer compilers and such
- Use libsmbios on some systems to enable firmware updates (Mario Limonciello)
- Use the correct reset type from the QueryCapsuleInfo data
- Lots of fixes from auditing
- Use efivar's error reporting infrastructure

* Fri Aug 12 2016 Adam Williamson <awilliam@redhat.com> - 0.5-5
- backport a couple of commits to fix build against efivar 26

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Nov 18 2015 Peter Jones <pjones@redhat.com> - 0.5-3
- Temporarily don't require shim on i?86 - we've never built it there, and
  libfwup knows how to handle it not being there just fine.

* Wed Nov 18 2015 Peter Jones <pjones@redhat.com> - 0.5-2
- Fix missing -libs Requires: due to editing error

* Wed Nov 18 2015 Peter Jones <pjones@redhat.com> - 0.5-1
- Rebase to 0.5
- Highlights in 0.5:
  - fwupdate.efi is called fwup$EFI_ARCH.efi now so weird platforms can have
    them coexist.  "Platform" here might mean "distro tools that care about
    multilib".  Anyway, it's needed to support things like baytrail.
  - Worked around shim command line bug where we need to treat LOAD_OPTIONS
    differently if we're invoked from the shell vs BDS
  - various debug features - SHIM_DEBUG and FWUPDATE_VERBOSE UEFI variables
    that'll let you get some debugging info some times
  - oh yeah, the actual debuginfo is useful
  - Automatically cleans up old instances on fresh OS installs
  - valgrind --leak-check=full on fwupdate doesn't show any errors at all
  - covscan shows only two things; one *really* doesn't matter, the other is
    because it doesn't understand our firmware variable data structure and
    can't work out that we have guaranteed the length of some data in a code
    path it isn't considering.
  - fwup_set_up_update() API improvements
  - killed fwup_sterror() and friends entirely
  - Should work on x64, ia32, and aarch64.

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 02 2015 Peter Jones <pjones@redhat.com> - 0.4-1
- Update to 0.4
- Set DESTDIR so it's more consistently respected
- Always use upper case for Boot#### names.
- Create abbreviated device paths for our BootNext entry.
- Make subdir Makefiles get the version right.
- Fix ucs2len() to handle max=-1 correctly.
- Compare the right blobs when we're searching old boot entries.
- Fix .efi generation on non-x86 platforms.
- Use a relative path for fwupdate.efi when launched from shim.
- Show fewer debugging messages.
- Set BootNext when we find an old Boot#### variable as well.
- Add fwup_get_fw_type().

* Mon Jun 01 2015 Peter Jones <pjones@redhat.com> - 0.3-4
- Make abbreviated device paths work in the BootNext entry.
- Fix a ucs2 parsing bug.

* Mon Jun 01 2015 Peter Jones <pjones@redhat.com> - 0.3-3
- Always use abbreviated device paths for Boot#### entries.

* Mon Jun 01 2015 Peter Jones <pjones@redhat.com> - 0.3-2
- Fix boot entry naming.

* Thu May 28 2015 Peter Jones <pjones@redhat.com> - 0.3-1
- Here we go again.

# vim:expandtab
