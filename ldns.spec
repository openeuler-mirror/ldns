%global _hardened_build 1
%global with_python3 1

%bcond_without  perl
%bcond_without  ecdsa

%bcond_without  eddsa
%bcond_without  dane_ta

%bcond_with     gost

%{?!snapshot:         %global snapshot        0}

%if %{with_python3}
%{?filter_setup:
%global _ldns_internal_filter /^_ldns[.]so.*/d;
%filter_from_requires %{_ldns_internal_filter}
%filter_from_provides %{_ldns_internal_filter}
%filter_setup
}
%global _ldns_internal _ldns[.]so[.].*
%global __requires_exclude ^(%{_ldns_internal})$
%global __provides_exclude ^(%{_ldns_internal})$
%endif

%if %{with perl}
%{?perl_default_filter}
%endif

Name: 		ldns
Version: 	1.7.0
Release: 	27
Summary:        Low-level DNS(SEC) library with API

License: 	BSD
Url: 		https://www.nlnetlabs.nl/projects/%{name}/about/
Source0:        https://www.nlnetlabs.nl/downloads/%{name}/%{name}-%{version}.tar.gz

Patch1: 	%{name}-1.7.0-parse-limit.patch
Patch2: 	%{name}-1.7.0-realloc.patch
Patch3: 	%{name}-1.7.0-Update-for-SWIG-4.patch

%if 0%{snapshot}
BuildRequires: 	libtool autoconf automake 
%endif

BuildRequires: 	gcc make libpcap-devel gcc-c++ doxygen gdb
%if %{with dane_ta}
BuildRequires: 	openssl-devel >= 1.1.0
%else
BuildRequires: 	openssl-devel >= 1.0.2k
%endif

%if %{with_python3}
BuildRequires: 	python3-devel, swig
%endif
%if %{with perl}
BuildRequires: 	perl-devel perl-ExtUtils-MakeMaker 
BuildRequires: 	perl-generators perl(Devel::CheckLib)
%endif
Requires: 	ca-certificates

%description
The goal of ldns is to simplify DNS programming, it supports recent RFCs 
like the DNSSEC documents, and allows developers to easily create software 
conforming to current RFCs, and experimental software for current Internet 
Drafts. A secondary benefit of using ldns is speed; ldns is written in C 
it should be a lot faster than Perl.

%package 	devel
Summary: 	Development files for %{name}
Requires:  	%{name} = %{version}-%{release}
Requires: 	pkgconfig openssl-devel

Provides:       %{name}-utils
Obsoletes:      %{name}-utils

%description 	devel
%{name}-devel contains the header files for developing
applications that want to make use of %{name}.

%if %{with python3}
%package 	-n python3-%{name}
Summary: 	Python3 extensions for %{name}
Requires: 	%{name} = %{version}-%{release}
%{?python_provide:%python_provide python3-%{name}}

%description 	-n python3-%{name}
Python3 packages for %{name}
%endif

%if %{with perl}
%package 	-n perl-%{name}
Summary: 	Perl information for %{name}
Requires: 	%{name} = %{version}-%{release}
Requires:  	perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%description 	-n perl-%{name}
Perl packages for %{name}
%endif

%package        help 
Summary:        Documents for %{name} 
Buildarch:      noarch 
Requires:	man info 

Provides:      	%{name}-doc
Obsoletes:      %{name}-doc

%description help 
Man pages and other related documents for %{name}. 

%prep
%{?extra_version:%global pkgname %{name}-%{version}%{extra_version}}%{!?extra_version:%global pkgname %{name}-%{version}}

%setup -qcn %{pkgname}
pushd %{pkgname}

%patch1 -p1 -b .limit
%patch2 -p1 -b .realloc
%patch3 -p1

%if 0%{snapshot}
  rm config.guess config.sub ltmain.sh
  aclocal
  libtoolize -c --install
  autoreconf --install
%endif

sed -i "s/@includedir@/@includedir@\/ldns/" packaging/libldns.pc.in

cp -pr doc LICENSE README* Changelog ../
cp -p contrib/ldnsx/LICENSE ../LICENSE.ldnsx
cp -p contrib/ldnsx/README ../README.ldnsx
popd

%if %{with python3}
mv %{pkgname} %{pkgname}_python3
%endif

%build
CFLAGS="%{optflags} -fPIC"
CXXFLAGS="%{optflags} -fPIC"
LDFLAGS="$RPM_LD_FLAGS -Wl,-z,now -pie"
export CFLAGS CXXFLAGS LDFLAGS

%if %{with gost}
  %global enable_gost --enable-gost
%else
  %global enable_gost --disable-gost
%endif

%if %{with ecdsa}
  %global enable_ecdsa --enable-ecdsa
%else
  %global enable_ecdsa --disable-ecdsa
%endif

%if %{with eddsa}
  %global enable_eddsa --enable-ed25519 --enable-ed448
%else
  %global enable_eddsa --disable-ed25519 --disable-ed448
%endif

%if ! %{with dane_ta}
  %global disable_dane_ta --disable-dane-ta-usage
%endif

%global common_args \\\
  --disable-rpath \\\
  %{enable_gost} %{enable_ecdsa} %{enable_eddsa} %{?disable_dane_ta} \\\
  --with-ca-file=/etc/pki/tls/certs/ca-bundle.trust.crt \\\
  --with-ca-path=/etc/pki/tls/certs/ \\\
  --with-trust-anchor=%{_sharedstatedir}/unbound/root.key \\\
  --disable-static \\\


%if 0%{with_python3}
pushd %{pkgname}_python3
%else
pushd %{pkgname}
%endif 

%configure \
  %{common_args} \
  --with-examples \
  --with-drill \
%if %{with_python3}
  --with-pyldns PYTHON=%{__python3}
%endif

make %{?_smp_mflags}
make %{?_smp_mflags} doc

%if %{with perl}
  pushd contrib/DNS-LDNS
  LD_LIBRARY_PATH="../../lib:$LD_LIBRARY_PATH" perl \
      Makefile.PL INSTALLDIRS=vendor  INC="-I. -I../.." LIBS="-L../../lib"
  make
  popd
%endif

sed -i "s~$RPM_LD_FLAGS~~" packaging/ldns-config
popd

%install
rm -rf %{buildroot}

%if %{with_python3}
pushd %{pkgname}_python3
%else
pushd %{pkgname}
%endif

make DESTDIR=%{buildroot} INSTALL="%{__install} -p" install
make DESTDIR=%{buildroot} INSTALL="%{__install} -p" install-doc

%delete_la
%if %{with_python3}
rm -rf %{buildroot}%{python3_sitearch}/*.la
%endif

install -D -m644  packaging/libldns.pc %{buildroot}%{_libdir}/pkgconfig/ldns.pc
%if %{with perl}
  make -C contrib/DNS-LDNS DESTDIR=%{buildroot} pure_install
  chmod 755 %{buildroot}%{perl_vendorarch}/auto/DNS/LDNS/LDNS.so
  rm -f %{buildroot}%{perl_vendorarch}/auto/DNS/LDNS/{.packlist,LDNS.bs}
%endif
popd

rm doc/*.xml

rm doc/doxyparse.pl

rm -rf doc/man

%ldconfig_scriptlets

%files
%defattr(-,root,root)
%license LICENSE
%{_bindir}/%{name}-config
%{_libdir}/libldns.so.*

%files devel
%defattr(-,root,root)
%{_bindir}/drill
%{_bindir}/ldnsd
%{_bindir}/%{name}-*
%{_libdir}/libldns.so
%{_libdir}/pkgconfig/%{name}.pc
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.h

%if %{with_python3}
%files -n python3-ldns
%defattr(-,root,root)
%license LICENSE.ldnsx
%{python3_sitearch}/*
%endif

%if %{with perl}
%files -n perl-ldns
%defattr(-,root,root)
%{perl_vendorarch}/*
%exclude %dir %{perl_vendorarch}/auto/DNS/
%endif

%files help
%defattr(-,root,root)
%doc doc README Changelog README.git
%{_mandir}/man1/*
%{_mandir}/man3/*.3.gz
%if %{with_python3}
%doc %{pkgname}_python3/contrib/python/Changelog README.ldnsx
%endif
%if %{with perl}
%{_mandir}/man3/*
%endif

%changelog
* Thu Oct 29 2020 gaihuiying <gaihuiying1@huawei.com> - 1.7.0-27
- Type:rquirement
- ID:NA
- SUG:NA
- DESC:remove python2, don't support python2 anymore

* Mon Aug 03 2020 gaihuiying <gaihuiying1@huawei.com> - 1.7.0-26
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:fix build fail with swig new version

* Sat Mar 22 2020 openEuler Buildyeam <buildteam@openeuler.org> - 1.7.0-25
- fix build bug,add flag with_python2 and with_python3

* Sat Jan 11 2020 openEuler Buildyeam <buildteam@openeuler.org> - 1.7.0-23
- Delete useless info

* Sat Sep 21 2019 openEuler Buildteam <buildteam@openeuler.org> - 1.7.0-22
- Package init
