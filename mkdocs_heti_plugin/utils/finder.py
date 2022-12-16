import bs4

def substring(text, start, end = None):
    if end is None:
        end = len(text)
    start = max(0, start)
    end = max(0, end)
    if (start > end):
        return text[end:start]
    return text[start:end]

class Finder:
    def __init__(self, soup, node, options: dict):
        if not options.get("offset"):
            options["offset"] = 0
        self.soup = soup
        self.node = node
        self.options = options
        self.matches = self.search()
        if self.matches:
            self.processMatches()
    
    def search(self):
        self._matchIndex = 0
        self._offset = 0
        self._regex = self.options["find"]
        self._textAggregation = self.getAggregateText()
        self._matches = []

        def matchAggregation(textAggregation):
            for text in textAggregation:
                if not isinstance(text, str):
                    matchAggregation(text)
                    continue
                startPos = 0
                while match := self._regex.match(text, startPos):
                    self._matches.append(self.prepMatch(match, self._matchIndex, self._offset))
                    self._matchIndex += 1
                    startPos = match.end()
                self._offset += len(text)
        
        matchAggregation(self._textAggregation)
        return self._matches

    def prepMatch(self, match, matchIndex, characterOffset):
        if not match.group():
            raise Exception("cannot handle zero-length matches")
        d = dict()
        d["text"] = match.group(1)
        d["endIndex"] = characterOffset + match.end(1)
        d["startIndex"] = characterOffset + match.start(1)
        d["index"] = matchIndex
        d["match"] = match
        return d
    
    def getAggregateText(self):
        self._elementFilter = self.options["filterElements"]
        self._forceContext = self.options["forceContext"]

        def getText(node):
            if isinstance(node, bs4.element.NavigableString):
                return [str(node)]
            if self._elementFilter and (not self._elementFilter(node)):
                return []
            txt = ['']
            for child in node.children:
                if isinstance(child, bs4.element.NavigableString):
                    txt[-1] += str(child)
                    continue
                innerText = getText(child)
                if (
                    self._forceContext and 
                    isinstance(child, bs4.element.Tag) and
                    self._forceContext(child)
                ):
                    txt.append(innerText)
                    txt.append('')
                else:
                    if len(innerText) > 0 and isinstance(innerText[0], str):
                        txt[-1] += innerText.pop(0)
                    if len(innerText):
                        txt.append(innerText)
                        txt.append('')
            return txt
        
        return getText(self.node)
    
    def processMatches(self):
        matches = self.matches
        node = self.node
        elementFilter = self.options["filterElements"]
        startPortion = None
        endPortion = None
        innerPortions = []
        curNode = node
        match = matches.pop(0)
        atIndex = 0
        portionIndex = 0
        doAvoidNode = None
        nodeStack = [node]

        while True:
            if isinstance(curNode, bs4.element.NavigableString):
                if (not endPortion) and (len(curNode) + atIndex >= match["endIndex"]):
                    endPortion = Portion(
                        node = curNode,
                        index = portionIndex,
                        text = substring(curNode.string, match["startIndex"] - atIndex + self.options["offset"], match["endIndex"] - atIndex),
                        indexInMatch = 0 if atIndex == 0 else atIndex - match["startIndex"],
                        indexInNode = match["startIndex"] - atIndex + self.options["offset"],
                        endIndexInNode = match["endIndex"] - atIndex,
                        isEnd = True
                    )
                    portionIndex += 1
                elif startPortion:
                    innerPortions.append(Portion(
                        node = curNode,
                        index = portionIndex,
                        text = curNode.string,
                        indexInMatch = atIndex - match["startIndex"],
                        indexInNode = 0
                    ))
                    portionIndex += 1
                
                if (not startPortion) and (len(curNode) + atIndex > match["startIndex"]):
                    startPortion = Portion(
                        node = curNode,
                        index = portionIndex,
                        indexInMatch = 0,
                        indexInNode = match["startIndex"] - atIndex + self.options["offset"],
                        endIndexInNode = match["endIndex"] - atIndex,
                        text = substring(curNode.string, match["startIndex"] - atIndex + self.options["offset"], match["endIndex"] - atIndex),
                    )
                    portionIndex += 1
                
                atIndex += len(curNode.string)
            
            doAvoidNode = isinstance(curNode, bs4.element.Tag) and elementFilter and (not elementFilter(curNode))

            if startPortion and endPortion:
                curNode = self.replaceMatch(match, startPortion, innerPortions, endPortion)
                atIndex -= (len(endPortion.node.string) - endPortion.endIndexInNode)
                startPortion = None
                endPortion = None
                innerPortions = []
                match = matches.pop(0) if len(matches) else None
                portionIndex = 0
                if match is None:
                    break
            elif (not doAvoidNode) and (hasattr(curNode, "children") or hasattr(curNode, "next_sibling")):
                if hasattr(curNode, "children") and len(list(curNode.children)) > 0:
                    nodeStack.append(curNode)
                    curNode = list(curNode.children)[0]
                else:
                    curNode = curNode.next_sibling
                continue
                
            while True:
                if hasattr(curNode, "next_sibling") and curNode.next_sibling:
                    curNode = curNode.next_sibling
                    break
                curNode = nodeStack.pop()
                if curNode == node:
                    return
    
    def replaceMatch(self, match, startPortion, innerPortions, endPortion):
        matchStartNode = startPortion.node
        matchEndNode = endPortion.node
        preceedingTextNode = None
        followingTextNode = None
        if matchStartNode == matchEndNode:
            node = matchStartNode
            if startPortion.indexInNode > 0:
                preceedingTextNode = substring(node.string, 0, startPortion.indexInNode)
                node.insert_before(self.soup.new_string(preceedingTextNode))
            newNode = self.getPortionReplacementNode(endPortion, match)
            node.insert_before(newNode)
            if endPortion.endIndexInNode < len(node.string):
                followingTextNode = substring(node.string, endPortion.endIndexInNode)
                node.insert_before(self.soup.new_string(followingTextNode))
            node.extract()
            return newNode
        else:
            preceedingTextNode = substring(matchStartNode.string, 0, startPortion.indexInNode)
            followingTextNode = substring(matchEndNode.string, endPortion.endIndexInNode)
            firstNode = self.getPortionReplacementNode(startPortion, match)
            innerNodes = []
            for portion in innerPortions:
                innerNode = self.getPortionReplacementNode(portion, match)
                portion.node.replace_with(innerNode)
                innerNodes.append(innerNode)
            lastNode = self.getPortionReplacementNode(endPortion, match)
            matchStartNode.insert_before(self.soup.new_string(preceedingTextNode))
            matchStartNode.insert_before(firstNode)
            matchStartNode.extract()
            matchEndNode.insert_before(lastNode)
            matchEndNode.insert_before(self.soup.new_string(followingTextNode))
            matchEndNode.extract()
            return lastNode
    
    def getPortionReplacementNode(self, portion, match=None):
        replacement = self.options["replace"] if self.options.get("replace") else "$&"
        if callable(replacement):
            if portion.text == " ":
                return self.soup.new_string("")
            # print(f"replacement(portion={portion}, match={match})")
            replacement = replacement(portion, self.soup)
            if replacement and isinstance(replacement, bs4.element.Tag):
                return replacement
            return self.soup.new_string(replacement)


class Portion():
    def __init__(
        self,
        node = None,
        index = None,
        text = None,
        indexInMatch = None,
        indexInNode = None,
        endIndexInNode = None,
        isEnd = None
    ):
        self.node = node
        self.index = index
        self.text = text
        self.indexInMatch = indexInMatch
        self.indexInNode = indexInNode
        self.endIndexInNode = endIndexInNode
        self.isEnd = isEnd
