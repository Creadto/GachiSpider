import re
from .base import Base
from typing import Dict, List, Tuple


class Matcher(Base):
    def __init__(self, mass: str, name = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"):
        """Robots.txt parser, Validate url with crawler's name

        Args:
            mass (str): Raw text of robots.txt
            name (str, optional): Crawler name. If you have multiple names, not implemented. Defaults to "*".
        """
        super(Matcher, self).__init__(mass=mass, name=name)
        self.bot_name = 'user-agent:' + name
        mass = mass.lower().replace(' ', '')
        search = mass.find(self.bot_name)
        if search == -1:
            self.bot_name = 'user-agent:*'
        self.rules = self.update_policy(mass.splitlines())
    
    def update_policy(self, policies: List[str]) -> Dict[str, object]:
        """Making rules that fitted my crawler

        Args:
            policies (List[str]): Separated lines from robots.txt

        Returns:
            Dict[str, object]: Allow domains, Disallow domains, and other options
        """
        rules = {'allow': [], 'disallow': []}
        in_group = False
        for line in policies:
            if in_group == False:
                in_group = self._in_bot(line)
            else:
                result = self._put_rules(self._get_key_value(line), rules)
                if result == None:
                    in_group = self._in_bot(line)
                else:
                    rules = result
        
        return rules
        
    def allow_by(self, url: str, progressive=True) -> Tuple[bool, str]:
        """Sanity check that can visit the url

        Args:
            url (str): url
            progressive (bool): In the case where a URL is not covered by either disallow or allow, this option will be returned.
        Returns:
            Tuple[bool, str]: Allow = True and Condition
        """
        rtn_value = {'allow': True, 'disallow': False}
        
        for key, conds in self.rules.items():
            for cond in conds:
                result = re.search(cond, url)
                if result is not None:
                    return rtn_value[key], cond
            
        return progressive, None
    
    def _put_rules(self, kv, rules):
        key, value = kv
        if key == "lf" or key == "user-agent":
            if (len(rules['disallow']) + len(rules['allow'])) > 0:
                return None
        else:
            if key not in rules:
                rules[key] = value
            else:
                if isinstance(rules[key], list):
                    rules[key].append(value)
        return rules
        
                    
    def _get_key_value(self, line: str):
        if line == '':
            return "lf", None
        
        stubs = line.split(':')
        key = stubs[0].lower()
        value = "".join(stubs[1:])
        pre = value.find('/')
        if pre != -1:
            value = value[pre:]
        return key, value
    
    def _in_bot(self, line: str):
        line = line.replace(' ', '')
        return self.bot_name == line.lower()