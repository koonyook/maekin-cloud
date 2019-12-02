Summary: Maekin Computing Library
Name: maekin-lib
Version: 0.1
Release: 1
Group: maekin
License: GPL
AutoReqProv: no
Vendor: HPCNC, Kasetsart University, Thailand.
Packager: Znut <znut@hpcnc.com>
BuildArch: noarch

%description
This package contain Maekin Library
 
%prep
rm -rf %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/
 
%install
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/distro
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/middleware
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/managementtool
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/var/storage/images
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/var/storage/templates

cp -r %{_sourcedir}/distro/*  %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/distro/
cp -r %{_sourcedir}/middleware/*  %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/middleware/
cp -r %{_sourcedir}/managementtool/*  %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/managementtool/
touch %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/var/dhcp-middleware.conf
touch %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/var/dhcp-distro.conf

%files
%defattr(755, -, -, 755) 
/maekin

%clean
