%global version           @PKG_VERSION@
%global release           @PKG_RELEASE@
%global hash              @PKG_HASH@
%global pgsql_major       @PG_VERSION@
%global pgsql_full        @PG_FULL_VERSION@
%global edition           @EDITION@
%global edition_full      @EDITION_FULL@
%global prefix            @PREFIX@

Name:           pg_probackup-%{edition}-%{pgsql_major}
Version:        %{version}
Release:        %{release}.%{hash}
Summary:        Backup utility for PostgresPro %{edition_full}
Group:          Applications/Databases
License:        BSD
Url:            http://postgrespro.ru/
#Source0:        postgrespro-%{edition}-%{pgsql_full}.tar.bz2
#Source1:        pg_probackup-%{version}.tar.bz2
Source0:        postgrespro-%{edition}-%{pgsql_full}
Source1:        pg_probackup-%{version}
BuildRequires:  gcc make perl glibc-devel bison flex
BuildRequires:  readline-devel openssl-devel gettext zlib-devel


%description
Backup tool for PostgresPro %{edition_full}.

%prep
#%setup -q -b1 -n pg_probackup-%{version}.tar.bz2
mv %{_topdir}/SOURCES/postgrespro-%{edition}-%{pgsql_full} %{_topdir}/BUILD
cd %{_topdir}/BUILD/postgrespro-%{edition}-%{pgsql_full}
mv %{_topdir}/SOURCES/pg_probackup-%{version} contrib/pg_probackup

mkdir %{_topdir}/SOURCES/postgrespro-%{edition}-%{pgsql_full}
mkdir %{_topdir}/SOURCES/pg_probackup-%{version}

%build
#cd %{_topdir}/SOURCES/postgrespro-%{edition}-%{pgsql_full}
#mv %{_topdir}/SOURCES/postgrespro-%{edition}-%{pgsql_full} ./
#cd postgrespro-%{edition}-%{pgsql_full}
#mv %{_topdir}/SOURCES/pg_probackup-%{version} contrib/pg_probackup
cd %{_topdir}/BUILD/postgrespro-%{edition}-%{pgsql_full}

%if "%{pgsql_major}" == "9.6"
./configure --enable-debug
%else
./configure --enable-debug --prefix=%{prefix}
%endif
make -C 'src/common'
make -C 'src/port'
make -C 'src/interfaces'
cd contrib/pg_probackup && make

%install
cd %{_topdir}/BUILD/postgrespro-%{edition}-%{pgsql_full}
%{__mkdir} -p %{buildroot}%{_bindir}
%{__install} -p -m 755 contrib/pg_probackup/pg_probackup %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Wed Feb 9 2018 Grigory Smolkin <g.smolkin@postgrespro.ru> - %{version}-%{release}.%{hash}
- @PKG_VERSION@

* Fri Jan 29 2018 Grigory Smolkin <g.smolkin@postgrespro.ru> - 2.0.14-1
- Initial release.
