import os

import mysql.connector


class MysqlWrapper:

    @staticmethod
    def get_connection_writer():
        mysql_conn = mysql.connector.connect(
            host='wordtwitsdb.chsq9glns06n.us-west-2.rds.amazonaws.com',
            user='stocktwits_sys',
            passwd=os.environ.get('MYSQL_PASSWORD'),
            db='WordTwitsDatabase'
        )

        return mysql_conn

    @staticmethod
    def get_connection_rr():
        mysql_conn = mysql.connector.connect(
            host='wordtwitsdb-rr.chsq9glns06n.us-west-2.rds.amazonaws.com',
            user='stocktwits_sys',
            passwd=os.environ.get('MYSQL_PASSWORD'),
            db='WordTwitsDatabase'
        )

        return mysql_conn