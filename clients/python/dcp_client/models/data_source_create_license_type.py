from enum import StrEnum


class DataSourceCreateLicenseType(StrEnum):
    CUSTOMER_TERMS = "customer_terms"
    EMPLOYEE_NOTICE = "employee_notice"
    LICENSED = "licensed"
    OPEN_LICENSE = "open_license"
    OTHER = "other"
    OWNED = "owned"
    VENDOR_AGREEMENT = "vendor_agreement"

    def __str__(self) -> str:
        return str(self.value)
