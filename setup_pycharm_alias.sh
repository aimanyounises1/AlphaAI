#!/bin/bash

# Determine the shell configuration file
if [ -n "$ZSH_VERSION" ]; then
    config_file="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    config_file="$HOME/.bash_profile"
else
    echo "Unsupported shell. Please use zsh or bash."
    exit 1
fi

# Add the PyCharm alias to the configuration file
echo "alias pycharm=\"open -a /Applications/PyCharm.app/Contents/MacOS/pycharm .\"" >> "$config_file"

# Source the configuration file
source "$config_file"

echo "PyCharm alias has been added to $config_file and sourced."
echo "You can now use the 'pycharm' command to open PyCharm from any directory."