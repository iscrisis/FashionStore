docker : pg_dump: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  database 
"test_db" does not exist
En línea: 6 Carácter: 1
+ docker exec fashionstore-postgres_test-1 pg_dump -U test_user -d test ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (pg_dump: error:... does not exist:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
