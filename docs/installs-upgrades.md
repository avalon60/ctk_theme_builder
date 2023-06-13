# Requirements

You must have Python installed. The recommended version of Python is 3.10, although anything above Python 3.8 should suffice. 

Note the application has not been tested against Python 3.11. 

The application has been tested on Linux Mint and Windows 10, although there is no obvious reason as to why it shouldn't work on MacOS or other Linux ports.

You will require around 160MB of disk space.

## Ubuntu Based Linux Distributions

For Ubuntu based distros (e.g. Linux Mint, Elementary OS, Zorin OS...), ,
Please ensure that you have ensurepip installed. This can be installed via the command:

`apt install python3.10-venv`

## Installation

### The theme\_builder\_setup.py Utility
Installations and upgrades are performed using the <i>theme\_builder\_setup.py</i> utility. In situ upgrades or patching can be performed using <i>theme\_builder\_setup.py</i>, but it can also install/upgrade from a package in the form of a ZIP file. This latter method, using a ZIP package, is the recommended way to install or update the application.

The <i>theme\_builder\_setup.py</i> utility expects a parent directory to be supplied. For new installations, using a ZIP package, it will create a sub-directory, *ctk\_theme\_builder*, in which the application is installed. 

To obtain a list of options, run the command:  
  
  `python theme_builder_setup.py -h`
  
Note that with some Python installations, you may need to run the above command with *python3*, instead of *python*.

## ZIP Packages

To obtain a ZIP package, look at the available releases of CTk Theme Builder, on the GitHub project page. The installable archives start with "ctk\_theme\_builder-", followed by the version, and ending with .zip. For example: <i>ctk\_theme\_builder-2.0.0.zip`</i>

Install using the following steps:  
  
1. From the zip file, extract the theme\_builder\_setup.py file.
2. Run the install command using both the -i and -a flags.

You need a command window to run the setup utility. On windows, you should be able to right click a folder in Windows Explorer, and select _CMD Prompt Here_. Another option is to click the Windows search (bottom left) and where it says _Type search here_, enter the commend _CMD_ and press _Enter_. There is also a further option, simply enter the text _CMD_, into the navigation field at the top of Windows Explorer and press Enter.

For Linux, you can open a Terminal. This is often available as a menu option, but if not, you may need to Google the subject for your specific Linux distribution. 

Example:

`python theme_builder_setup.py -i /home/clive/utilities -a /tmp/ctk_theme_builder-2.0.0.zip`

In the example, the utilities folder, is just an arbitrary parent folder location, which must be created in advance.

If one doesn't already exist, this will cause a ctk\_theme\_builder directory to be created, below the utilities folder. The ZIP file will be unpacked to the folder and the application will be set up into an executable state. 

  If there is already an installation of ctk\_theme\_builder, below the specified installation location, theme\_builder\_setup.py will attempt an upgrade.   
  
  If the installation is already at the same version as that contained in the ZIP archive, the theme\_builder\_setup.py will run in a "fix" mode. For example if you have accidentally removed your venv folder, it will fix it.
  
# Launching CTk Theme Builder
There are a number of options, for launching CTk Theme Builder, and these vary slightly depending on the operating system. One common method for them all is to launch using the *ctk\_theme\_builder* command. The most basic way is to open a CMD/Terminal window and type in a command. 

For example, if you had installed CTk Theme Builder in a ``/u01/utilities/ctk_theme_builder`folder, then you could launch, using the following:-  
  
Linux/MacOS example:  

`/u01/utilities/ctk_theme_builder/ctk_theme_builder`
  
Windows example:  

`C:\utilities\ctk_theme_builder\ctk_theme_builder`

On Windows, the above should cause the *ctk\_theme\_builder.bat* file, located in the CTk Theme builder application home directory to be executed. 

On Linux and MacOS, the *ctk\_theme\_builder* is a hard link to *ctk\_theme\_builder.sh*. 

The upshot is that you can also invoke a launch of CTk Theme Builder with *ctk\_theme\_builder.bat* or *ctk\_theme\_builder.sh*, depending on your operating system.

If you open the CMD/Terminal window inside the *ctk\_theme\_builder* folder, then instead of typing the full pathname, you could simply type:  
  
`./ctk_theme_builder` (Linux / MacOS)  
	
OR

`.\ctk_theme_builder` (Windows)

## PATH Variable
If you don't want to include the path-name to the CTk Theme Builder script, you can always change your operating system PATH variable, to include the installation directory. You may need to Google how to do this, based on whichever operating system you are using.

## Desktop Launchers
Most operating systems, with a Graphical User Interface, tend to provide a launcher mechanism which can be set up on the desktop. 

For example, you can create a desktop shortcut on Windows, in order to launch the *ctk\_theme\_builder* script described earlier. Linux ports tend to have similar(ish) facilities. 

You'll need to Google how to set up a shortcut / launcher for your specific operating system. 
