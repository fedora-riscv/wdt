%bcond_without static
# The tests work but they rely on strict timing, which makes them flaky when
# run in koji, so keep them disabled for now
%bcond_with tests

# last tagged release is from 2016 despite ongoing development
%global commit 57bbd437075324892620ffa38d6c207f4acdd714
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global date 20210809

%global _shared_builddir shared_build
%global _static_builddir static_build

Name:           wdt
Version:        1.32.1910230
Release:        %autorelease -s %{?date}git%{?shortcommit}
Summary:        Warp speed Data Transfer

License:        BSD
URL:            https://www.facebook.com/WdtOpenSource
Source0:        https://github.com/facebook/wdt/archive/%{commit}/%{name}-%{commit}.tar.gz

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
%autochangelog
