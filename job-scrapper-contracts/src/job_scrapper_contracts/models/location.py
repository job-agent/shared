from dataclasses import dataclass
from typing import Optional, TypedDict


class LocationDict(TypedDict):
    region: Optional[str]
    is_remote: bool
    can_apply: Optional[bool]


@dataclass
class Location:
    """Job location information

    Attributes:
        region: Geographic region or country for the job
        can_apply: Indicates whether the user can apply for this job based on location.
            - True: User can apply (bi-check2-circle or bi-question-circle icon)
            - False: User cannot apply (bi-x-circle icon)
            - None: Status unknown or not available
    """

    region: Optional[str] = None
    is_remote: bool = False
    can_apply: Optional[bool] = None
