# Infograb
A python script that harvest info, then it takes the info and upload it to a usb drive. As simple as that

#How to compile to .exe:
1. Install python from https://www.python.org/downloads/
2. Open command prompt and run "pip install pyinstaller" (Ensure that python and pip is added to the environmental variables, although this should be done automaticly)
3. Download the infograb.py file and right click on it and click on "Copy as path" (In Windows 10 you might need to shift right click to see the option)
4. Run the command "pyinstaller --onefile C:\path\to\infograb.py" change the filepath to the one you copied. This will create the .exe file, you will find it in a new folder names dist, it will be in the folder that the python script is in.

