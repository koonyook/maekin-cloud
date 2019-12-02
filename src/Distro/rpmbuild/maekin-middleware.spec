Summary: Maekin Middleware Library
Name: maekin-middleware
Version: 0.1
Release: 1
Group: maekin
License: GPL
AutoReqProv: no
Vendor: HPCNC, Kasetsart University, Thailand.
Packager: Znut <znut@hpcnc.com>
BuildArch: noarch

%description
This package contain libraries of Maekin Middleware

%prep
rm -rf %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/middleware
 
%install
mkdir -p %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/middleware
cp -r %{_sourcedir}/middleware/*  %{_buildrootdir}/%{name}-%{version}-%{release}.x86_64/maekin/lib/middleware/
 
%files
%defattr(755, -, -, 755) 
/maekin/lib/middleware

%clean
