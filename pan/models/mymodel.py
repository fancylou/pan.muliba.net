from sqlalchemy import (
    ForeignKey,
    Column,
    Index,
    Integer,
    Text,
    String,
)

from .meta import Base


class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    value = Column(Integer)


Index('my_index', MyModel.name, unique=True, mysql_length=255)


class User(Base):
    __tablename__ = 'pan_users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    password = Column(String(128))
    email = Column(String(256))
    phone = Column(String(25))

    def to_dic(self):
        return dict(id=self.id, username=self.username, email=self.email, phone=self.phone)


class Folder(Base):
    __tablename__ = 'pan_folders'
    id = Column(Integer, primary_key=True)
    pid = Column(Integer)
    uid = Column(Integer, ForeignKey('pan_users.id'))
    name = Column(String(256))
    createTime = Column(Integer)
    updateTime = Column(Integer)


# 存放bucketNumber 默认生成一个1024 ，如果满了 递增 基本满不了 100w文件一个桶
class Bucket(Base):
    __tablename__ = 'pan_buckets'
    id = Column(Integer, primary_key=True)
    bucketNumber = Column(Integer)
    bucketName = Column(String(50))


# 存储在服务器上的文件，id = (bucketNumber*1000000)递增 它同时也是存储路径 4层目录结构 1024000000=1024/0/0/0
class SourceFile(Base):
    __tablename__ = 'pan_source_files'
    id = Column(Integer, primary_key=True)
    extension = Column(String(20))
    size = Column(Integer)
    md5 = Column(String(256))


class File(Base):
    __tablename__ = 'pan_files'
    id = Column(Integer, primary_key=True)
    pid = Column(Integer)
    uid = Column(Integer,  ForeignKey('pan_users.id'))
    sfId = Column(Integer, ForeignKey('pan_source_files.id'))
    filename = Column(String(256))
    createTime = Column(Integer)
    updateTime = Column(Integer)




