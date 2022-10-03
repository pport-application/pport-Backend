# pport-Backend

## Installation and SETUP

The suggested IDE is PyCharm for this project and the instructions will be given accordingly.

Please execute the following commands to clone the repository. 
If you are seeing this repository, it is assumed that you already have access to read and write. Hence, please provide credentials to clone the repo.

```
  git clone git@github.com:pport-application/pport-Backend.git
```

The next, thing that needs to be done is to set the Python interpreter in PyCharm, so, venv's python will be utilized as well as other packages installed in the project's scope.

*File | Settings | Project: pport-Backend | Python Interpreter for Windows and Linux* <br />
*PyCharm | Preferences | Project: pport-Backend | Python Interpreter for macOS* <br />
 
Please add a new interpreter by clicking the setting icon and then add.

Inside *Virtualenv Environment | New Environment* add a new path which is */LOCATION/OF/YOUR/REPOSITORY/pport_Backend/venv* <br />

Close the Settings/Preferences page and go to *Edit Configuration* on the left side of run.

```
Script Path: */LOCATION/OF/YOUR/REPOSITORY/pport_Backend/manage.py* <br />
Parameters: *runserver* <br />
Python Interpreter: (Select your project interpreter added recently as */LOCATION/OF/YOUR/REPOSITORY/pport_Backend/venv* <br />
```

Now, you are ready to develop the project.

## Additional Instructions

The project is encapsulated with [venv]("https://docs.python.org/3/library/venv.html"), so, to install the package within the project's scope, please activate venv and then install the packages.
The commands for activating venv are as follows.

```
  cd pport-Backend
  source ./venv/bin/activate
```

## Git Documentation

Please do not make changes in **main** branch. Create a new branch from developing and merge back when you are done.

A detailed explanation for the branches is given below.

![project structure](https://github.com/pport-application/pport-Backend/blob/master/project_structure.png)
