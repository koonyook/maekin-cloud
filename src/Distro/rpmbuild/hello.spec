Summary: hello
Name: hello
Version: 1
Release: 1
Source0: hello.c
License: GPL
Group: Applications/Tools
Packager: Duncan Brown <duncan@duncanbrown.org>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
URL: http://magi2.cpe.ku.ac.th

%description
just hello, World!!

%prep
%build
gcc -o /home/znut/hello/hello /home/znut/hello/hello.c
%install
./hello
