etchub web gui.
=

```
git clone --recursive https://github.com/etchub/www.git
pip3 install -r www/requirements.txt
python3 -m www
```

or

```
git clone --recursive https://github.com/etchub/www.git
cd www
docker build --tag=etchub .
docker run -p 80:5555 etchub
```
