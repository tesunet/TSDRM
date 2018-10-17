************Linux系统下，运行程序前需要安装wkhtmltopdf启动程序，用以生成pdf文件************
1.下载地址：https://wkhtmltopdf.org/downloads.html
2.安装依赖(ubuntu16.4为例):sudo apt-get -f install xfonts-75dpi
3.安装wkhtmltopdf:dpkg -i wkhtmltox_0.12.5-1.xenial_amd64.deb


************Ubuntu系统下部署环境 apache+mod_wsgi************

1.准备依赖包/安装包
wget http://mirror.bit.edu.cn/apache/httpd/httpd-2.4.35.tar.gz
wget http://mirror.bit.edu.cn/apache/apr/apr-1.6.5.tar.gz
wget http://mirror.bit.edu.cn/apache/apr/apr-util-1.6.1.tar.gz 
wget https://sourceforge.net/projects/pcre/files/pcre/8.41/pcre-8.41.tar.gz/download   # 下载后修改文件名:mv download pcre-8.41.tar.gz 
wget https://pypi.python.org/packages/28/a7/de0dd1f4fae5b2ace921042071ae8563ce47dac475b332e288bc1d773e8d/mod_wsgi-4.5.7.tar.gz


2.解压/编译/安装
tar -xzvf apr-1.6.5.tar.gz
tar -xzvf apr-util-1.6.1.tar.gz
tar -xzvf pcre-8.41.tar.gz
tar -xzvf httpd-2.4.35.tar.gz
tar -xzvf mod_wsgi-4.5.7.tar.gz

# 进入文件目录/编译安装/退出文件目录
cd apr-1.6.5
sudo ./configure --prefix=/usr/local/apr
sudo make
sudo make install
cd ..

cd apr-util-1.6.1
sudo ./configure --prefix=/usr/local/apr-util --with-apr=/usr/local/apr/bin/apr-1-config
sudo make
sudo make install
cd ..

cd pcre-8.41
sudo ./configure --prefix=/usr/local/pcre
sudo make
sudo make install
cd ..

cd httpd-2.4.29 
sudo ./configure --prefix=/usr/local/apache --with-pcre=/usr/local/pcre --with-apr=/usr/local/apr --with-apr-util=/usr/local/apr-util
sudo make
sudo make install
cd ..


# 添加/修改配置:
# httpd.conf文件中添加ServerName localhost:80
sudo vi /usr/local/apache/conf/httpd.conf +193

# 启动/测试apache
sudo /usr/local/apache/bin/apachectl start 

# 查看apache启动状况
ps -ajx|grep apache  # 关闭apache:sudo /usr/local/apache/bin/apachectl stop


2.安装/配置mod_wsgi(将mod_wsgi关联apache与python，启动apache时会自动调用mod_wsgi与python)
cd mod_wsgi-4.5.7/
sudo ./configure --with-apxs=/usr/local/apache/bin/apxs --with-python=/usr/bin/python3
sudo make 
sudo make install  # 相关报错处理(当前无报错)：./configure --prefix=/usr/local/ CFLAGS=-fPIC
chmod 755 /usr/local/apache/modules/mod_wsgi.so


3.配置apache
  3.1
	# 取消注释：#Include conf/extra/httpd-vhosts.conf
	# 加上LoadModule wsgi_module modules/mod_wsgi.so
	sudo vi /usr/local/apache/conf/httpd.conf 
  3.2
	# 编辑/usr/local/apache/conf/extra/httpd-vhosts.conf
	sudo vi /usr/local/apache/conf/extra/httpd-vhosts.conf
	# 注释掉原本配置，添加下面配置:
		<VirtualHost *:8000>
		        DocumentRoot /var/www/html/TSDRM/TSDRM
		                WSGIScriptAlias / /var/www/html/TSDRM/TSDRM/wsgi.py

		        <Directory /var/www/html/TSDRM/TSDRM>
		                AllowOverride All
		                Require all granted
		        </Directory>
		</VirtualHost>
		Alias /static /var/www/html/TSDRM/faconstor/static
		<Directory /var/www/html/TSDRM/faconstor/static>
		        AllowOverride None
		        Options None
		        Require all granted
		</Directory>


4.启动/重新启动apache
sudo /usr/local/apache/bin/apachectl start # restart


5.访问项目:http://ip:port

