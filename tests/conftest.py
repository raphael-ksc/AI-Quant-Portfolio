def pytest_configure(config):
    config.addinivalue_line('markers', 'mysql: 需要真的 MySQL（設定 MYSQL_TEST_DATABASE 才會執行）')
