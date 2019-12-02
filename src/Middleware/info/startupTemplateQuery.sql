INSERT INTO `templates` 
	(`fileName`, `OS`, `size`, `description`, `minimumMemory`, `maximumMemory`)
VALUES
('winxp-base.img', 'WindowsXP SP3', '8589934592', 'Simple and ready to be used. Please start from remote desktop', '200', '2048'),
('ubuntu-base.img', 'Ubuntu10.04 LTS', '8589934592', 'Simple and ready to be used. Please start from SSH', '384', '2048'),
('centos6-base.img', 'CentOS 6.2 Minimal', '8589934592', 'lightweight VM for general usage', '200', '2048'),
('centos6-dev-base.img', 'CentOS 6.2 Dev', '8589934592', 'template for developer works', '200', '2048'),
('centos6-web-base.img', 'CentOS 6.2 Web', '8589934592', 'template for create web server', '200', '2048');
