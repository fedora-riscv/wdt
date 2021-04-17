%bcond_without static
# The tests work but they rely on strict timing, which makes them flaky when
# run in koji, so keep them disabled for now
%bcond_with tests

# last tagged release is from 2016 despite ongoing development
%global commit fdbc5432230290f86ff8ad89ab52d5b7fef232b4
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global date 20210331

%global _shared_builddir shared_build
%global _static_builddir static_build

Name:           wdt
Version:        1.32.1910230
Release:        5.%{?date}git%{?shortcommit}%{?dist}
Summary:        Warp speed Data Transfer

License:        BSD
URL:            https://www.facebook.com/WdtOpenSource
Source0:        https://github.com/facebook/wdt/archive/%{commit}/%{name}-%{commit}.tar.gz
# WDT uses C++17 features starting with fdbc5432230290f86ff8ad89ab52d5b7fef232b4
Patch0:         wdt-require_cxx17.patch

BuildRequires:  gcc-c++
BuildRequires:  cmake

# folly is disabled on s390x
ExcludeArch:    s390x

BuildRequires:  boost-devel
BuildRequires:  double-conversion-devel
BuildRequires:  folly-devel
BuildRequires:  gflags-devel
BuildRequires:  glog-devel
BuildRequires:  gtest-devel
BuildRequires:  jemalloc-devel
BuildRequires:  openssl-devel
%if %{with static}
BuildRequires:  folly-static
%endif
%if %{with tests}
BuildRequires:  bash
BuildRequires:  python3
%endif

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
# for wcp
Requires:       bash

%description
Warp speed Data Transfer is aiming to transfer data between two systems
as fast as possible.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package        libs
Summary:        Shared libraries for %{name}

%description    libs
Warp speed Data Transfer (WDT) is a library aiming to transfer data between
two systems as fast as possible over multiple TCP paths.

%if %{with static}
%package        static
Summary:        Static development libraries for %{name}
Requires:       %{name}-devel%{?_isa} = %{version}-%{release}

%description    static
The %{name}-static package contains static libraries for
developing applications that use %{name}.
%endif

%prep
%setup -c -q
# wdt needs to be build from a base directory called wdt
# https://github.com/facebook/wdt/issues/213
ln -s %{name}-%{commit} %{name}
pushd %{name} >/dev/null
%patch0 -p1
popd >/dev/null
# Disable hardcoded CXX FLAGS
sed -i -e 's/set(CMAKE_CXX_FLAGS.*//' %{name}/CMakeLists.txt

%build
mkdir %{_shared_builddir}
pushd %{_shared_builddir}
%cmake ../%{name} \
  -DCMAKE_CXX_FLAGS="%{optflags}" \
  -DCMAKE_SKIP_RPATH=ON \
  -DBUILD_SHARED_LIBS=ON \
  -DWDT_USE_SYSTEM_FOLLY=ON \
%if %{with tests}
  -DBUILD_TESTING=ON
%else
  -DBUILD_TESTING=OFF
%endif
%cmake_build
popd

%if %{with static}
mkdir %{_static_builddir}
pushd %{_static_builddir}
%cmake ../%{name} \
  -DCMAKE_CXX_FLAGS="%{optflags}" \
  -DCMAKE_SKIP_RPATH=ON \
  -DBUILD_SHARED_LIBS=OFF \
  -DWDT_USE_SYSTEM_FOLLY=ON \
  -DBUILD_TESTING=OFF
%cmake_build
popd
%endif

%install
pushd "%{_shared_builddir}"
%cmake_install
# move installed shared libraries in the right place if needed
%if "%{_lib}" == "lib64"
mv %{buildroot}%{_prefix}/lib %{buildroot}%{_libdir}
%endif
popd

%if %{with static}
pushd %{_static_builddir}
# Not using %%cmake_install here as we need to override the DESTDIR
DESTDIR="%{buildroot}/static" %__cmake --install "%{__cmake_builddir}"
# move installed static libraries in the right place
mv %{buildroot}/static%{_prefix}/lib/*.a %{buildroot}%{_libdir}
rm -rf %{buildroot}/static
popd
%endif

%if %{with tests}
%check
pushd %{_shared_builddir}
# tests are linked against a bunch of shared libraries
export LD_LIBRARY_PATH="$PWD/%{__cmake_builddir}"
%ctest
popd
%endif

%files
%doc wdt/README.md
%license wdt/LICENSE
%{_bindir}/wdt
%{_bindir}/wcp

%files devel
%{_includedir}/*
%{_libdir}/*.so

%files libs
%{_libdir}/*.so.1*

%if %{with static}
%files static
%{_libdir}/*.a
%endif

%changelog
* Fri Apr 16 2021 Michel Alexandre Salim <salimma@fedoraproject.org> - 1.32.1910230-5.20210331gitfdbc543
- Update to snapshot from 20210331

* Mon Mar 29 2021 Michel Alexandre Salim <salimma@fedoraproject.org> - 1.32.1910230-5.20210312git97a8c0a
- Rebuild against folly 2021.03.29.00

* Wed Mar 24 2021 Michel Alexandre Salim <salimma@fedoraproject.org> - 1.32.1910230-4.20210312git97a8c0a
- Rebuild against folly 2021.03.22.00

* Mon Mar 15 2021 Michel Alexandre Salim <salimma@fedoraproject.org> - 1.32.1910230-3.20210312git97a8c0a
- Update to 20210312

* Tue Mar  9 2021 Davide Cavalca <dcavalca@fedoraproject.org> - 1.32.1910230-2.20210128git6aec23c
- Fix typos in summary
- Use more strict globbing for the soname version

* Thu Jan 28 2021 Davide Cavalca <dcavalca@fedoraproject.org> - 1.32.1910230-1.20210128git6aec23c
- Bump git commit to include upstream fixes
- Use system folly instead of bundling it
- Default to shared library build
- Use %%cmake instead of %%cmake3
- Use %%bcond for tests and turn off by default due to flakiness
- Update BuildRequires and Requires

* Sat Nov 07 2020 Nicolas Chauvet <kwizart@gmail.com> - 1.32.1910230-2.20200909gitb585d21
- Improve description
- Add --with tests conditional for tests
- Switch to cmake3
- And ExcludeArch inherited from folly

* Fri Oct 23 2020 Nicolas Chauvet <kwizart@gmail.com> - 1.32.1910230-1.20200909gitb585d21
- Update to 1.32.1910230 snapshot

* Tue Dec 19 2017 Kees de Jong <keesdejong@fedoraproject.org> - 1.27.1612021-1
- Initial package
