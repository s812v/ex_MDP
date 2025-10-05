import collections
from src.protocols import *
# Incoming Message
class IncomingMessage(object):
    """ INCOMING MESSAGE from various sources to RPi
    it needs to be decoded and parsed to be used
    it has a header, message type and data
    each of these is a string and separated by a newline
    
    data is a string "data1, data2, data3, ..."
    header is a string "ARD" or "ALG" or "AND" or "RSP"
    type is dependent on the header
    """
    def __init__(self, message, source_header, from_outgoing=False, target_header=None, data_type=None):
        if not from_outgoing:
            message = message.decode()
            self.message = message
            self.message_list = self.message.split('|')
            
            self._target_header = self.message_list[0]
            self._source_header = source_header
            self._data_type = self.message_list[1]
            self._data = self.message_list[2]
            
            if self._target_header not in ALL_HEADERS:
                raise ValueError('Invalid header')
        if from_outgoing:
            self._data = message
            self._target_header = target_header
            self._data_type = data_type
            self._source_header = source_header
        
    @classmethod
    def from_outgoingmessage(cls, outgoing):
        return cls(
            outgoing.data, 
            outgoing.source_header,
            from_outgoing=True, 
            target_header=outgoing.target_header,
            data_type=outgoing.data_type
        )
    
    def __str__(self):
        return self.message
    
    @property
    def source_header(self):
        return self._source_header
    
    @property
    def target_header(self):
        return self._target_header

    @property
    def data_type(self):
        return self._data_type
    
    @property
    def data(self):
        return self._data
    
    @property
    def encoded(self):
        return self.message.encode()
    
    def set_target_header(self, target_header):
        self._target_header = target_header
    
    def set_data_type(self, data_type):
        self._data_type = data_type
    

class OutgoingMessage(object):
    """ OUTGOING MESSAGE from RPi to target devices
    it is stored as a string and needs to be encoded before sending
    it has a source, target, message type and data
    
    data is a string "data1, data2, data3, ..."
    header is a string "ARD" or "ALG" or "AND" or "RSP"
    source is the header of the sender
    type is dependent on the source header
    """
    def __init__(self,
                 source_header,
                 target_header, 
                 data_type,
                 data):
        
        self._data = data
        self._source_header = source_header
        self._target_header = target_header
        self._data_type = data_type
        self.message_encoded = False
        if self._source_header not in ALL_HEADERS:
            raise ValueError('Invalid header')
        if self._target_header not in ALL_HEADERS:
            raise ValueError('Invalid header')
        if isinstance(self._data, str):
            self.message = '|'.join([self._source_header, self._data_type, self._data])
        elif isinstance(self._data, bytes):
            self.message = self._data
            self.message_encoded = True
    
    @property
    def source_header(self):
        return self._source_header
    
    @property
    def target_header(self):
        return self._target_header

    @property
    def data_type(self):
        return self._data_type
    
    @property
    def data(self):
        return self._data
    
    @property
    def encoded(self):
        if self.message_encoded:
            return self.message
        return self.message.encode()
    
class DequeProxy(object):
    def __init__(self, *args):
        self.deque = collections.deque(*args)
    def __len__(self):
        return self.deque.__len__()
    def appendleft(self, x):
        self.deque.appendleft(x)
    def append(self, x):
        self.deque.append(x)
    def popleft(self):
        return self.deque.popleft()