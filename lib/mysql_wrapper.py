import os

import mysql.connector


class MysqlWrapper:

    @staticmethod
    def get_connection():
        mysql_conn = mysql.connector.connect(
            host='wordtwitsdb.chsq9glns06n.us-west-2.rds.amazonaws.com',
            user='stocktwits_sys',
            passwd=os.environ.get('MYSQL_PASSWORD'),
            db='WordTwitsDatabase'
        )

        return mysql_conn
