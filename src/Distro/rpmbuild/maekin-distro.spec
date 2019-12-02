Summary: Maekin Distro Library
Name: maekin-distro
Version: 0.1
Release: 1
Group: maekin
License: GPL
AutoReqProv: no
Vendor: HPCNC, Kasetsart University, Thailand.
Packager: Znut <znut@hpcnc.com>
BuildArch: noarch

%description
This package contain Maekin - Distro Library
 
%prep
rm -rf %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/distro
 
%install
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/distro
cp -r %{_sourcedir}/distro/*  %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/distro/
 
%files
%defattr(755, -, -, 755) 
/maekin/lib/distro/

%clean
