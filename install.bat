:: NOTE: This is a batch script to install and try out ElectionAudits
:: NOTE: http://neal.mcburnett.org/electionaudits/

:: NOTE: You first need to obtain "wget" and 7-Zip and put them in these
:: NOTE: places, or adjust the script based on where you put them.
:: NOTE: C:\Program Files\wget.exe
:: NOTE: C:\Program Files\7-Zip\7z.exe

rd audit-build /s /q
mkdir audit-build
cd audit-build



:: ********** Install wget **********
"%ProgramFiles%\wget" http://www.interlog.com/~tcharron/wgetwin-1_5_3_1-binary.zip
"%ProgramFiles%\7-Zip\7z" x wgetwin-1_5_3_1-binary.zip
copy wget.exe "%ProgramFiles%"



:: ********** Install Python **********

"%ProgramFiles%\wget" http://www.python.org/ftp/python/2.5.2/python-2.5.2.msi
python-2.5.2.msi



:: ********** Install Django **********
"%ProgramFiles%\wget" http://www.djangoproject.com/download/1.0/tarball/

"%ProgramFiles%\7-Zip\7z" e Django-1.0.tar.gz
"%ProgramFiles%\7-Zip\7z" x Django-1.0.tar
rd c:\Django /s /q
move Django-1.0 c:\Django

pushd c:\Django
C:\Python25\python setup.py install
popd



:: ********** Install lxml **********
"%ProgramFiles%\wget" http://pypi.python.org/packages/2.5/s/setuptools/setuptools-0.6c9.win32-py2.5.exe
setuptools-0.6c9.win32-py2.5.exe
C:\Python25\Scripts\easy_install lxml



:: ********** Install sqlite **********
"%ProgramFiles%\wget" http://www.sqlite.org/sqlitedll-3_6_4.zip
"%ProgramFiles%\7-Zip\7z" e sqlitedll-3_6_4.zip

move sqlite3.dll "%WINDIR%\system32"
pushd "%WINDIR%\system32"
regsvr32.exe /s sqlite3.dll
popd 



:: ********** Setup django **********
pushd ..\root

C:\Python25\python manage.py test electionaudits

C:\Python25\python manage.py syncdb

C:\Python25\python manage.py parse
C:\Python25\python manage.py runserver
popd

:: NOTE: reset before trying to repeat parse steps, like this:
:: C:\Python25\python manage.py reset electionaudits

cd ..
