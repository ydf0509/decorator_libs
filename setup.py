# coding=utf-8
from pathlib import Path
from setuptools import setup, find_packages

# with open("README.md", "r",encoding='utf8') as fh:
#     long_description = fh.read()

# filepath = ((Path(__file__).parent / Path('README.md')).absolute()).as_posix()
filepath = 'README.md'
print(filepath)

setup(
    name='decorator_libs',  #
    version="1.2",
    description=(
        'all kinds of decorators'
    ),
    keywords=("pysnooper", 'decorator'),
    # long_description=open('README.md', 'r',encoding='utf8').read(),
    long_description_content_type="text/markdown",
    long_description=open(filepath, 'r', encoding='utf8').read(),
    # data_files=[filepath],
    author='bfzs',
    author_email='m13148804508@163.com',
    maintainer='ydf',
    maintainer_email='m13148804508@163.com',
    license='BSD License',
    packages=find_packages(),
    include_package_data=True,
    platforms=["all"],
    url='',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=['nb_log',
                      'pysnooper',
                      'pysnooper_click_able',
                      'tomorrow3',
                      'flask'
                      ]
)
"""
打包上传
python setup.py sdist upload -r pypi


python setup.py sdist & twine upload dist/decorator_libs-1.2.tar.gz



python -m pip install decorator_libs --upgrade -i https://pypi.org/simple   # 及时的方式，不用等待 阿里云 豆瓣 同步
"""
