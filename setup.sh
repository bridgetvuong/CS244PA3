cd ~/
git clone git://github.com/noxrepo/pox
git checkout 0a1bbb8

cd ~/
sudo apt-get install -y python-setuptools
git clone git://github.com/brandonheller/ripl.git
cd ripl
sudo python setup.py develop

cd ~/
git clone git://github.com/brandonheller/riplpox.git
cd riplpox
sudo python setup.py develop

cd ~/CS244PA3/mininet
sudo python setup.py install

cd ~/CS244PA3
