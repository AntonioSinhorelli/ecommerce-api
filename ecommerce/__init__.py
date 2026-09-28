# Usa o PyMySQL (driver MySQL 100% Python) no lugar do mysqlclient.
# Assim o deploy no Elastic Beanstalk não precisa compilar nada (gcc / mariadb-devel)
# para conectar no RDS MySQL.
try:
    import pymysql

    pymysql.version_info = (2, 2, 1, 'final', 0)  # versão mínima exigida pelo Django 6
    pymysql.__version__ = '2.2.1'
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
