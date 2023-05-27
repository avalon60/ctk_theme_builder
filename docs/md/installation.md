# CTk Theme Builder Installation

## Requirements

You must have Python installed. The minimum recommended version of Python is 3.10. 

The application has been tested on Linux Mint and Windows 10, although there is no obvious reason as to why it shouldn't work on MacOS or other Linux ports.

You will require at least 160MB of disk space.

## Installation

### The theme\_builder\_setup.py Utility
Installations and upgrades are performed using the <i>theme\_builder\_setup.py</i> utility. In situ upgrades can be performed using <i>theme\_builder\_setup.py</i>, but it can also install/upgrade from a package in the form of a ZIP file.

The <i>theme\_builder\_setup.py</i> utility expects a parent directory to be supplied. For new installations, using a ZIP package, it will create a sub-directory, ctk_theme_builder, in which the application is installed. 

To obtain a list of options, run the command:  
  
  `python theme\_builder\_setup.py -h`
  
Note that with some Python installations, you may need to run the above command with __python3_, instead of _python_.

### Cloned Copy

If you want to get a cloned copy of the repository, up an running, you will need to run the supplied <i>theme\_builder\_setup.py</i> utility as an in-situ install. 

Example:

You have cloned the project to:

`/home/clive/utilities/ctk\_theme\_builder`

To build the app you would need to run the command:  

`python theme\_builder\_setup.py -i /home/clive/utilities`

### ZIP Package

If you have a ZIP package (a specific archive format is required), then you can install, using the following steps:  
  
1. From the zip file, extract the theme\_builder\_setup.py file.
2. Run the install command using both the -a and -h flags.

Example:

`python theme\_builder\_setup.py -i /home/clive/utilities -a /tmp/ctk_theme_builder-2.0.0.zip`

This will cause a ctk\_theme\_builder directory to be created (if it doesn't already exist), below the utilities folder. The ZIP file will be unpacked to the folder and the application will be set up into a runnable state. 

  If there is already an installation of ctk\_theme\_builder, below the specified installation location, theme\_builder\_setup.py will attempt an upgrade.   
  
  If the installation is already at the same version as that contained in the ZIP archive, the theme\_builder\_setup.py will run in a "fix" mode. For example if you have accidentally removed your venv folder, it will fix it.
  

  
   