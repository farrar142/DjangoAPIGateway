from rest_framework import exceptions


class ConflictException(exceptions.APIException):
    status_code = exceptions.status.HTTP_409_CONFLICT
    default_detail = {"not_implemented": ["정의되지 않은 오류입니다. 백엔드 개발자에게 에러내용을 추가해 달라고하세요"]}


class TimeoutException(exceptions.APIException):
    status_code = exceptions.status.HTTP_504_GATEWAY_TIMEOUT
    default_detail = {"timeout": ["현재 연결이 많아 지연됩니다. 다시 시도해 주세요."]}


class GenericException(exceptions.APIException):
    status_code = exceptions.status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = {"unavailable": ["현재 서비스 이용이 불가합니다."]}


class TokenExpiredExcpetion(exceptions.APIException):
    status_code = exceptions.status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = {"token": ["토큰이 만료되었습니다."]}
