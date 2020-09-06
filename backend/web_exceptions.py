class WebException(Exception):
    message = "Undefined web exception"
    code = 400

    def __init__(self, message=""):
        super().__init__(message)
        self.detail_message = message

    @property
    def error_dict(self):
        return {
            "errorCode": self.code,
            "errorTitle": self.message,
            "errorDescription": self.detail_message
        }


class ProjectNotFoundException(WebException):
    code = 404
    message = "Project not found"

class ProjectAlreadyExistsException(WebException):
    message = "Cannot create new project in folder with existing project"

class BlankFileNameException(WebException):
    message = "Resource not selected for uploading"

class MissingFileException(WebException):
    code=404
    message = "File not found"

class FileAlreadyExistsException(WebException):
    message = "A file with the same name as the file you are importing already exists in the project folder"

class FileTypeNotSupportedException(WebException):
    message = "This file type is currently not supported"

# possibly to be deleted
class InvalidYAMLFileException(WebException):
    message = "YAML file is either empty or not valid"
