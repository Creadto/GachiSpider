from abc import ABCMeta, abstractmethod
import logging
from typing import Dict, List, Tuple


class Base(metaclass=ABCMeta):
    def __init__(self, mass: str, name = "*"):
        """Robots.txt parser, Validate url with crawler's name

        Args:
            mass (str): Raw text of robots.txt
            name (str, optional): Crawler name. If you have multiple names, not implemented. Defaults to "*".
        """
        self.logger = logging.getLogger(name="matcher")
        self.name = name
        
    @abstractmethod
    def update_policy(self, policies: List[str]) -> Dict[str, object]:
        """Making rules that fitted my crawler

        Args:
            policies (List[str]): Separated lines from robots.txt

        Returns:
            Dict[str, object]: Allow domains, Disallow domains, and other options
        """
        pass
    
    @abstractmethod
    def allow_by(self, url: str, progressive=True) -> Tuple[bool, str]:
        """Sanity check that can visit the url

        Args:
            url (str): url
            progressive (bool): In the case where a URL is not covered by either disallow or allow, this option will be returned.
        Returns:
            Tuple[bool, str]: Allow = True and Condition
        """
        pass