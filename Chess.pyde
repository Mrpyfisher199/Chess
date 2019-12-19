from copy import copy

def setup():
    #We set the size to 11*32, if ever changed, change the 32, not the 11.
    size(11*32,11*32)
    global WHITE, BLACK, View, isPressed
    #We import the font
    l = createFont("PTMono-Bold",32)
    textFont(l)
    #We have the setup timer
    print minute(),second()
    #Maybe there's a better way, idk, but for now, we need this to store whether or not
    #The mouse has been pressed and is still pressed.
    isPressed = Variable(False)
    #Basically we check if we should render the possible moves for a selected spot.
    View = Variable([False,None])
    #We initiate the White and Black sides.
    WHITE = SIDE("W")
    BLACK = SIDE("B")
    #We make a "shortcut" reference to each side in each side, 
    #so that we can always refer to the enemy correctly.
    WHITE.enemy = BLACK
    BLACK.enemy = WHITE
    #We make sure that all the squares in both sides are coorrectly known as occupied or not.
    WHITE.setOccupied()
    BLACK.setOccupied()
    #We check all the spots that the other king wouldn't be able to cross.
    WHITE.setChecked()
    BLACK.setChecked()
    print minute(),second()
    frameRate(60)
  
#Blacks and Whites
class SIDE(list):
    def __init__(self,side):
        #Should be either W or B
        self.side = side
        sides = {"W":[7,6],"B":[0,1]}
        self.sides = sides
        #List of positions under attack
        self.checked = []
        #Lists all the positions in its side which are occupied by its own pieces.
        self.occupied = []
        #The enemy reference point... I guess it's like a pointer of sorts.
        self.enemy = None
        #We summon the images into the dictionary.
        self.pieces = {"pawn" : loadImage("pieces/pawn"+side+".png","png"),
            "rook" : loadImage("pieces/rook"+side+".png","png"),
            "knight" : loadImage("pieces/knight"+side+".png","png"),
            "bishop" : loadImage("pieces/bishop"+side+".png","png"),
            "queen" : loadImage("pieces/queen"+side+".png","png"),
            "king" : loadImage("pieces/king"+side+".png","png")}
        #Each piece we add only has 3 values (except for the pawns),
        #Those being the [x,y] position on the board (Where [0,0] would be a8)
        #and the piece.
        #Pawns also have a check for whether or not they can be En Passant-ed
        #We add all 8 pawns.
        for i in xrange(8):
            self.append([[i,sides[side][1]],"pawn",1])
        #We add the leftmost rook.
        self.append([[0,sides[side][0]],"rook"])
        #We add the leftmost knight.
        self.append([[1,sides[side][0]],"knight"])
        #We add leftmost the bishop.
        self.append([[2,sides[side][0]],"bishop"])
        #We add the queen.
        self.append([[3,sides[side][0]],"queen"])
        #We add the king.
        self.append([[4,sides[side][0]],"king"])
        #We add the rightmost bishop.
        self.append([[5,sides[side][0]],"bishop"])
        #We add the rightmost knight.
        self.append([[6,sides[side][0]],"knight"])
        #And finally, we add the rightmost rook.
        self.append([[7,sides[side][0]],"rook"])
        #When need be, we give this a list of positions to which a certain piece can move to.
        self.legal = []
        #A register for if the king has moved.
        self.hasMoved = False
        #A register for if the leftmost rook has moved.
        self.hasMovedRook0 = False
        #A register for if the rightmost rook has moved.
        self.hasMovedRook1 = False
        #A check for if the king is in check.
        self.check = False
        #Whether or not we display the queening menu, 
        #as pawns can become any piece besides themselves or a king.
        self.menu = [False,[1,1]]
        #We set the turn order.
        if side == "W":
            self.turn = True
            self.flip = False
        else:
            self.flip = True
            self.turn = False
    
    #We update the En passant values for the pawns.
    def setPawnStance(self):
        for i in range(len(self)):
            if self.side == "W":
                if self[i][1] == "pawn":
                    if self[i][0][1] != 6:
                        self[i][2] = 0
            else:
                if self[i][1] == "pawn":
                    if self[i][0][1] != 1:
                        self[i][2] = 0
    #We get the kings position.
    def getKing(self):
        for i in self:
            if i[1] == "king":
                return i[0]
    #As the name implies, we get the index of any given position, 
    #and if the postition isn't in our side, then we return None.
    def getIndexOfPos(self,pos,where=None):
        try:
            for i in range(len(where)):
                if where[i][0] == pos:
                    return i
        except Exception as e:
            for i in range(len(self)):
                if self[i][0] == pos:
                    return i
        return None
    #We check if the piece is pinned, and if so, along which axis.
    def isPinned(self,pos):
        #The value we would return on default.
        toReturn = False
        #We get the amount of checks we are checked by currently.
        check = self.inCheck()
        #We get the index of the pos in the side.
        spot = self.getIndexOfPos(pos)
        #We basically remove the piece from the board.
        self[spot][0] = [-1,-1]
        #We reset the occupied spaces, 
        #as that's what the enmy uses to deduce the positions of our pieces.
        self.setOccupied()
        #We reset the enemies checked positions.
        self.enemy.setChecked()
        #We check if we would be under even more checks if we move a piece, thus making it pinned.
        toReturn = self.inCheck()-check
        #Then we bring everything bask to it's original state.
        self[spot][0] = pos
        self.setOccupied()
        self.enemy.setChecked()
        mode = 0
        if toReturn:
            #1: piece can move along X axis
            #2: piece can move along Y axis
            #3: piece can move along +X+Y axis
            #4: piece can move along +X-Y axis
            #We do all this based on the position of the king relative to the piece. 
            if pos[1] == self.getKing()[1]:
                mode = 1    
            if pos[0] == self.getKing()[0]:
                mode = 2
            if pos[0] > self.getKing()[0]:
                if pos[1] > self.getKing()[1]:
                    mode = 3
                elif pos[1] < self.getKing()[1]:
                    mode = 4
            elif pos[0] < self.getKing()[0]:
                if pos[1] > self.getKing()[1]:
                    mode = 4
                elif pos[1] < self.getKing()[1]:
                    mode = 3
        return mode
    
    #Function to check whether the presence of a piece on that spot would stop the current check.
    def suppose(self,newPosition,origin=None):
        if self.check:
            toReturn = True
            #We add the new position to the occupied array.
            self.occupied.append(newPosition)
            #In case we are given an origin, remove it.
            if origin != None:
                self.occupied.remove(origin)
            #We check if eating the piece would do anything.
            piece = self.checkEaten(newPosition)
            #We reset the checked positions of the enemy.
            self.enemy.setChecked()
            if origin == None:
                if self.inCheck():
                    toReturn = not toReturn
            else:
                if self.inCheck(newPosition):
                    toReturn = not toReturn
            #We remove the new position.
            self.occupied.pop()
            if origin != None:
                self.occupied.append(origin)
            if piece != None:
                self.enemy.append(piece)
            self.enemy.setChecked()
            return toReturn
        else:
            return True
    
    #We check how many sources are checking the king.
    def inCheck(self,mode=None):
        cnt = 0
        c = self.getChecked()
        for i in range(len(c)):
            if mode == None:
                if c[i] == self.getKing():
                    cnt +=1
            else:
                if c[i] == mode:
                    cnt +=1
        return cnt 
    
    #We return the legal spaces of the requested positions piece.
    def setLegal(self,i):
        self.legal = []
        if i[1] == "pawn":
            self.legal = self.legal+self.pawn(i[0],True)
        elif i[1] == "king":
            self.legal = self.legal+self.king(i[0],True)
            self.legal = self.legal+self.castleK(i[0])
            self.legal = self.legal+self.castleQ(i[0])
        elif i[1] == "knight":
            self.legal = self.legal+self.knight(i[0],True)
        elif i[1] == "rook":
            self.legal = self.legal+self.rook(i[0],True)
        elif i[1] == "bishop":
            self.legal = self.legal+self.bishop(i[0],True)
        elif i[1] == "queen":
            self.legal = self.legal+self.queen(i[0],True)
    #We set the checked spaces.
    def setChecked(self):
        self.checked = []
        for i in self:
            if i[1] == "pawn":
                self.checked = self.checked+self.pawn(i[0],False)
            elif i[1] == "king":
                self.checked = self.checked+self.king(i[0],False)
            elif i[1] == "knight":
                self.checked = self.checked+self.knight(i[0],False)
            elif i[1] == "rook":
                self.checked = self.checked+self.rook(i[0],False)
            elif i[1] == "bishop":
                self.checked = self.checked+self.bishop(i[0],False)
            elif i[1] == "queen":
                self.checked = self.checked+self.queen(i[0],False)
    #We check if one of our pieces overlaps the enemies piece, thus removing that enemy piece.
    def checkEaten(self,pos):
        if self.enemy.getIndexOfPos(pos) != None:
            p = self.enemy[self.enemy.getIndexOfPos(pos)]
            self.enemy.pop(self.enemy.getIndexOfPos(pos))
            return p
        return None
    #We add all the positions covered by our pieces to the occupied list.
    def setOccupied(self):
        self.occupied = []
        for i in self:
            self.occupied.append(i[0])
    #We basically update everything, starting with the enemy, 
    #and after we do that we check if our king is under check.
    def update(self,coords,View):
        self.enemy.check = False
        self.enemy.setPawnStance()
        #All the special pawn moves.
        if self.enemy[self.enemy.getIndexOfPos(View.var[1])][1] == "pawn":
            if self.enemy.side == "B":
                #Whether or not we bring up the queening menu.
                if coords[1] == 7:
                    self.enemy.menu = [True,coords]
                else:
                    self.enemy.flip = True
                    self.flip = False
                #Whether or not we have an en passant-er.
                if coords == [View.var[1][0]-1,View.var[1][1]+1] \
                    and coords not in self.occupied \
                    or coords == [View.var[1][0]+1,View.var[1][1]+1] \
                    and coords not in self.occupied:
                    del self[self.getIndexOfPos([coords[0],coords[1]-1])]
            if self.enemy.side == "W":
                if coords[1] == 0:
                    self.enemy.menu = [True,coords]
                else:
                    self.enemy.flip = True
                    self.flip = False
                if coords == [View.var[1][0]-1,View.var[1][1]-1] \
                    and coords not in self.occupied \
                    or coords == [View.var[1][0]+1,View.var[1][1]-1] \
                    and coords not in self.occupied:
                    del self[self.getIndexOfPos([coords[0],coords[1]+1])]
        else:
            self.enemy.flip = True
            self.flip = False
        if self.enemy[self.enemy.getIndexOfPos(View.var[1])][1] == "king" \
            and not self.enemy.hasMoved:
            #We check for castling requests.
            if coords[0] > 5:
                self.enemy[self.enemy.getIndexOfPos([7,coords[1]])][0] = [coords[0]-1,coords[1]]
            elif coords[0]<3:
                self.enemy[self.enemy.getIndexOfPos([0,coords[1]])][0] = [coords[0]+1,coords[1]]
            self.enemy.hasMoved = True
        #We check for rook movement.
        if self.enemy[self.enemy.getIndexOfPos(View.var[1])][1] == "rook" and coords[0] < 4:
            self.enemy.hasMovedRook0 = True
        if self.enemy[self.enemy.getIndexOfPos(View.var[1])][1] == "rook" and coords[0] > 3:
            self.enemy.hasMovedRook1 = True
        #we update everything.
        self.enemy[self.enemy.getIndexOfPos(View.var[1])][0] = coords
        self.enemy.setOccupied()
        self.enemy.setChecked()
        self.enemy.checkEaten(coords)
        self.setOccupied()
        self.setChecked()
        if self.inCheck():
            self.check = True
        else:
            self.check = False  
        self.enemy.setChecked()
        self.enemy.turn = 0
        self.turn = 1      
    #We render everything.
    def render(self):
        if self.side == "W" and self.flip or self.enemy.side == "W" and self.enemy.flip:
            translate(width,height)
            rotate(radians(180))
        for i in self:
            if self.side == "W" and self.flip or self.enemy.side == "W" and self.enemy.flip:
                pushMatrix()
                rotate(radians(180))
                translate(-width/11-i[0][0]*width/11-width*1.5/11,
                          -height/11-i[0][1]*height/11-height*1.5/11)
                image(self.pieces[i[1]],0,0)
                popMatrix()
            #We render each piece on our side.
            else:
                image(self.pieces[i[1]],i[0][0]*width/11+width*1.5/11,
                    i[0][1]*height/11+height*1.5/11)
        if self.turn:
            for i in self.legal:
                #We render the legal moves of the requested piece.
                fill(0,0,255,100)
                rect(i[0]*width/11+width*1.5/11,i[1]*height/11+height*1.5/11,
                     width/11,height/11)
            if self.inCheck():
                #We check if our king is in check.
                fill(255,0,0,100)
                rect(self.getKing()[0]*width/11+width*1.5/11,
                     self.getKing()[1]*height/11+height*1.5/11,width/11,height/11)
        if self.side == "W" and self.flip or self.enemy.side == "W" and self.enemy.flip:
            rotate(radians(180))
            translate(-width,-height)
    #We get the checked positions of the enemy.  
    def getChecked(self):
        return self.enemy.checked
    #We get the occupied positions of the enemy.
    def getOccupied(self):
        return self.enemy.occupied
    #We check the range of our piece, based on obstructions.
    def reach(self,startPos,endPos,legal=False):
        Eoccupied = self.getOccupied()
        cleared = []
        count = [None,None]
        rangeS = [int(sqrt((startPos[0]-endPos[0])**2))+1,
                  int(sqrt((startPos[1]-endPos[1])**2))+1]
        if startPos[0]>endPos[0]:
            count[0]=-1
        elif startPos[0]<endPos[0]:
            count[0]=1
        if startPos[1]>endPos[1]:
            count[1]=-1
        elif startPos[1]<endPos[1]:
            count[1]=1
        if count[0] == None and count[1] == None:
            return []
        pos = startPos
        cnt = 0
        if count[0] == None:
            #Vertical movement.
            x = startPos[0]
            for y in range(rangeS[1]):
                y*=count[1]
                #We stop if the spot is occupied by one of our own.
                if legal and [x,pos[1]+y] in self.occupied:
                    break
                if not self.check:
                    cleared.append([x,pos[1]+y])
                elif self.suppose([x,pos[1]+y]):
                    cleared.append([x,pos[1]+y])
                if [x,pos[1]+y] in Eoccupied or [x,pos[1]+y] in self.occupied:
                    break
        elif count[1] == None:
            #Horizontal movement.
            y = startPos[1]
            for x in range(rangeS[0]):
                x*=count[0]
                if legal and [pos[0]+x,y] in self.occupied:
                    break
                if not self.check:
                    cleared.append([pos[0]+x,y])
                elif self.suppose([pos[0]+x,y]):
                    cleared.append([pos[0]+x,y])
                if [pos[0]+x,y] in Eoccupied or [pos[0]+x,y] in self.occupied:
                    break
        else:
            #Diagonal movement.
            for x in range(rangeS[0]):
                y = x
                x*=count[0]
                y*=count[1]
                if legal and [pos[0]+x,pos[1]+y] in self.occupied:
                    break
                if not self.check:
                    cleared.append([pos[0]+x,pos[1]+y])
                elif self.suppose([pos[0]+x,pos[1]+y]):
                    cleared.append([pos[0]+x,pos[1]+y])
                if [pos[0]+x,pos[1]+y] in Eoccupied or [pos[0]+x,pos[1]+y] in self.occupied:
                    break
        return cleared
    #We check the legal or illegal spaces covered by or rechable by the king.
    def king(self,pos,legal):
        if not legal:
            cleared = []
            for i in [[pos[0]-1,pos[1]-1],
                [pos[0],pos[1]-1],
                [pos[0]+1,pos[1]-1],
                [pos[0]-1,pos[1]],
                [pos[0]+1,pos[1]],
                [pos[0]-1,pos[1]+1],
                [pos[0],pos[1]+1],
                [pos[0]+1,pos[1]+1]]:
                cleared.append(i)
            return cleared
        else:
            cleared = []
            for i in [[pos[0]-1,pos[1]-1],
                [pos[0],pos[1]-1],
                [pos[0]+1,pos[1]-1],
                [pos[0]-1,pos[1]],
                [pos[0]+1,pos[1]],
                [pos[0]-1,pos[1]+1],
                [pos[0],pos[1]+1],
                [pos[0]+1,pos[1]+1]]:
                if i not in self.occupied and self.suppose(i, pos) and i not in self.getChecked():
                    cleared.append(i)
            return cleared
    #We check the legal or illegal spaces covered by or rechable by the queen.  
    def queen(self,pos,legal):
        cleared = []
        if legal:
            if self.isPinned(pos):
                if self.isPinned(pos) == 1:
                    cleared = cleared+self.reach([pos[0]-1,pos[1]],[-1,pos[1]],legal)
                    cleared = cleared+self.reach([pos[0]+1,pos[1]],[8,pos[1]],legal)
                elif self.isPinned(pos) == 2:
                    cleared = cleared+self.reach([pos[0],pos[1]-1],[pos[0],-1],legal)
                    cleared = cleared+self.reach([pos[0],pos[1]+1],[pos[0],8],legal)
                elif self.isPinned(pos) == 3:
                    cleared = cleared+self.reach([pos[0]-1,pos[1]-1],[pos[0]-7,pos[1]-7],legal)
                    cleared = cleared+self.reach([pos[0]+1,pos[1]+1],[pos[0]+7,pos[1]+7],legal)
                elif self.isPinned(pos) == 4:
                    cleared = cleared+self.reach([pos[0]+1,pos[1]-1],[pos[0]+7,pos[1]-7],legal)
                    cleared = cleared+self.reach([pos[0]-1,pos[1]+1],[pos[0]-7,pos[1]+7],legal)
                return cleared
        cleared = cleared+self.reach([pos[0]-1,pos[1]],[-1,pos[1]],legal)
        cleared = cleared+self.reach([pos[0]+1,pos[1]],[8,pos[1]],legal)
        cleared = cleared+self.reach([pos[0],pos[1]-1],[pos[0],-1],legal)
        cleared = cleared+self.reach([pos[0],pos[1]+1],[pos[0],8],legal)
        cleared = cleared+self.reach([pos[0]-1,pos[1]-1],[pos[0]-7,pos[1]-7],legal)
        cleared = cleared+self.reach([pos[0]+1,pos[1]-1],[pos[0]+7,pos[1]-7],legal)
        cleared = cleared+self.reach([pos[0]-1,pos[1]+1],[pos[0]-7,pos[1]+7],legal)
        cleared = cleared+self.reach([pos[0]+1,pos[1]+1],[pos[0]+7,pos[1]+7],legal)
        return cleared
    #We check the legal or illegal spaces covered by or rechable by the bishop.            
    def bishop(self,pos,legal):
        cleared = []
        if legal:
            if self.isPinned(pos):
                if self.isPinned(pos) == 3:
                    cleared = cleared+self.reach([pos[0]-1,pos[1]-1],[pos[0]-7,pos[1]-7],legal)
                    cleared = cleared+self.reach([pos[0]+1,pos[1]+1],[pos[0]+7,pos[1]+7],legal)
                elif self.isPinned(pos) == 4:
                    cleared = cleared+self.reach([pos[0]+1,pos[1]-1],[pos[0]+7,pos[1]-7],legal)
                    cleared = cleared+self.reach([pos[0]-1,pos[1]+1],[pos[0]-7,pos[1]+7],legal)
                return cleared
        cleared = cleared+self.reach([pos[0]-1,pos[1]-1],[pos[0]-7,pos[1]-7],legal)
        cleared = cleared+self.reach([pos[0]+1,pos[1]-1],[pos[0]+7,pos[1]-7],legal)
        cleared = cleared+self.reach([pos[0]-1,pos[1]+1],[pos[0]-7,pos[1]+7],legal)
        cleared = cleared+self.reach([pos[0]+1,pos[1]+1],[pos[0]+7,pos[1]+7],legal)
        return cleared
    #We check the legal or illegal spaces covered by or rechable by the knight.                
    def knight(self,pos,legal):
        if not legal:
            return [[pos[0]-1,pos[1]+2],
                    [pos[0]-1,pos[1]-2],
                    [pos[0]+1,pos[1]+2],
                    [pos[0]+1,pos[1]-2],
                    [pos[0]-2,pos[1]+1],
                    [pos[0]-2,pos[1]-1],
                    [pos[0]+2,pos[1]+1],
                    [pos[0]+2,pos[1]-1]]
        else:
            if self.isPinned(pos):
                return []
            cleared = []
            for i in [[pos[0]-1,pos[1]+2],
                [pos[0]-1,pos[1]-2],
                [pos[0]+1,pos[1]+2],
                [pos[0]+1,pos[1]-2],
                [pos[0]-2,pos[1]+1],
                [pos[0]-2,pos[1]-1],
                [pos[0]+2,pos[1]+1],
                [pos[0]+2,pos[1]-1]]:
                if i not in self.occupied and self.suppose(i):
                    cleared.append(i)
            return cleared
    #We check the legal or illegal spaces covered by or rechable by the rook.                
    def rook(self,pos,legal):
        cleared = []
        if legal:
            if self.isPinned(pos):
                if self.isPinned(pos) == 1:
                    cleared = cleared+self.reach([pos[0]-1,pos[1]],[-1,pos[1]],legal)
                    cleared = cleared+self.reach([pos[0]+1,pos[1]],[8,pos[1]],legal)
                elif self.isPinned(pos) == 2:
                    cleared = cleared+self.reach([pos[0],pos[1]-1],[pos[0],-1],legal)
                    cleared = cleared+self.reach([pos[0],pos[1]+1],[pos[0],8],legal)
                return cleared
        cleared = cleared+self.reach([pos[0]-1,pos[1]],[-1,pos[1]],legal)
        cleared = cleared+self.reach([pos[0]+1,pos[1]],[8,pos[1]],legal)
        cleared = cleared+self.reach([pos[0],pos[1]-1],[pos[0],-1],legal)
        cleared = cleared+self.reach([pos[0],pos[1]+1],[pos[0],8],legal)
        return cleared
    #We check the legal or illegal spaces covered by or rechable by the pawn. 
    #The movements change based on the side.   
    def pawn(self,pos,legal):
        if not legal:
            if self.side == "W":
                return [[pos[0]-1,pos[1]-1],[pos[0]+1,pos[1]-1]]
            else:
                return [[pos[0]-1,pos[1]+1],[pos[0]+1,pos[1]+1]]
        else:
            cleared = []
            if self.isPinned(pos):
                if self.side == "W":
                    if self.isPinned(pos) == 2 \
                        and [pos[0],pos[1]-1] not in self.getOccupied() \
                        and [pos[0],pos[1]-1] not in self.occupied:
                        if self.suppose([pos[0],pos[1]-1]):
                            cleared.append([pos[0],pos[1]-1])
                        if pos[1] == self.sides[self.side][1] \
                            and [pos[0],pos[1]-2] not in self.getOccupied() \
                            and [pos[0],pos[1]-2] not in self.occupied \
                            and self.suppose([pos[0],pos[1]-2]):
                            cleared.append([pos[0],pos[1]-2])
                    if self.isPinned(pos) == 3 and [pos[0]-1,pos[1]-1] in self.getOccupied():
                        if self.suppose([pos[0]-1,pos[1]-1]):
                            cleared.append([pos[0]-1,pos[1]-1])
                    if self.isPinned(pos) == 4 and [pos[0]+1,pos[1]-1] in self.getOccupied():
                        if self.suppose([pos[0]+1,pos[1]-1]):
                            cleared.append([pos[0]+1,pos[1]-1])
                    if self.isPinned(pos) == 3 and pos[1] == 3 \
                        and [pos[0]-1,pos[1]] in self.getOccupied():
                        if self.suppose([pos[0]-1,pos[1]]) \
                            and self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][1] == "pawn":
                            if self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][2]:
                                cleared.append([pos[0]-1,pos[1]-1])
                    if self.isPinned(pos) == 4 and pos[1] == 3 \
                        and [pos[0]+1,pos[1]] in self.getOccupied():
                        if self.suppose([pos[0]+1,pos[1]]) \
                            and self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][1] == "pawn":
                            if self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][2]:
                                cleared.append([pos[0]+1,pos[1]-1])
                else:
                    if self.isPinned(pos) == 2 \
                        and [pos[0],pos[1]+1] not in self.getOccupied() \
                        and [pos[0],pos[1]+1] not in self.occupied:
                        if self.suppose([pos[0],pos[1]+1]):
                            cleared.append([pos[0],pos[1]+1])
                        if pos[1] == self.sides[self.side][1] \
                            and [pos[0],pos[1]+2] not in self.getOccupied() \
                            and [pos[0],pos[1]+2] not in self.occupied \
                            and self.suppose([pos[0],pos[1]+2]):
                            cleared.append([pos[0],pos[1]+2])        
                    if self.isPinned(pos) == 4 and [pos[0]-1,pos[1]+1] in self.getOccupied():
                        if self.suppose([pos[0]-1,pos[1]+1]):
                            cleared.append([pos[0]-1,pos[1]+1])
                    if self.isPinned(pos) == 3 and [pos[0]+1,pos[1]+1] in self.getOccupied():
                        if self.suppose([pos[0]+1,pos[1]+1]):
                            cleared.append([pos[0]+1,pos[1]+1])    
                    if self.isPinned(pos) == 4 and pos[1] == 4 \
                        and [pos[0]-1,pos[1]] in self.getOccupied():
                        if self.suppose([pos[0]-1,pos[1]]) \
                            and self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][1] == "pawn":
                            if self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][2]:
                                cleared.append([pos[0]-1,pos[1]+1])
                    if self.isPinned(pos) == 3 and pos[1] == 4 \
                        and [pos[0]+1,pos[1]] in self.getOccupied():
                        if self.suppose([pos[0]+1,pos[1]]) \
                            and self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][1] == "pawn":
                            if self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][2]:
                                cleared.append([pos[0]+1,pos[1]+1])                    
                return cleared
            if self.side == "W":
                if [pos[0],pos[1]-1] not in self.getOccupied() \
                    and [pos[0],pos[1]-1] not in self.occupied:
                    if self.suppose([pos[0],pos[1]-1]):
                        cleared.append([pos[0],pos[1]-1])
                    if pos[1] == self.sides[self.side][1] \
                        and [pos[0],pos[1]-2] not in self.getOccupied() \
                        and [pos[0],pos[1]-2] not in self.occupied \
                        and self.suppose([pos[0],pos[1]-2]):
                        cleared.append([pos[0],pos[1]-2])
                if [pos[0]-1,pos[1]-1] in self.getOccupied():
                    if self.suppose([pos[0]-1,pos[1]-1]):
                        cleared.append([pos[0]-1,pos[1]-1])
                if [pos[0]+1,pos[1]-1] in self.getOccupied():
                    if self.suppose([pos[0]+1,pos[1]-1]):
                        cleared.append([pos[0]+1,pos[1]-1])
                if pos[1] == 3 and [pos[0]-1,pos[1]] in self.getOccupied():
                    if self.suppose([pos[0]-1,pos[1]]) \
                        and self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][1] == "pawn":
                        if self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][2]:
                            cleared.append([pos[0]-1,pos[1]-1])
                if pos[1] == 3 and [pos[0]+1,pos[1]] in self.getOccupied():
                    if self.suppose([pos[0]+1,pos[1]]) \
                        and self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][1] == "pawn":
                        if self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][2]:
                            cleared.append([pos[0]+1,pos[1]-1])
            else:
                if [pos[0],pos[1]+1] not in self.getOccupied() \
                    and [pos[0],pos[1]+1] not in self.occupied:
                    if self.suppose([pos[0],pos[1]+1]):
                        cleared.append([pos[0],pos[1]+1])
                    if pos[1] == self.sides[self.side][1] \
                        and [pos[0],pos[1]+2] not in self.getOccupied() \
                        and [pos[0],pos[1]+2] not in self.occupied \
                        and self.suppose([pos[0],pos[1]+2]):
                        cleared.append([pos[0],pos[1]+2])        
                if [pos[0]-1,pos[1]+1] in self.getOccupied():
                    if self.suppose([pos[0]-1,pos[1]+1]):
                        cleared.append([pos[0]-1,pos[1]+1])
                if [pos[0]+1,pos[1]+1] in self.getOccupied():
                    if self.suppose([pos[0]+1,pos[1]+1]):
                        cleared.append([pos[0]+1,pos[1]+1])    
                if pos[1] == 4 and [pos[0]-1,pos[1]] in self.getOccupied():
                    if self.suppose([pos[0]-1,pos[1]]) \
                        and self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][1] == "pawn":
                        if self.enemy[self.enemy.getIndexOfPos([pos[0]-1,pos[1]])][2]:
                            cleared.append([pos[0]-1,pos[1]+1])
                if pos[1] == 4 and [pos[0]+1,pos[1]] in self.getOccupied():
                    if self.suppose([pos[0]+1,pos[1]]) \
                        and self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][1] == "pawn":
                        if self.enemy[self.enemy.getIndexOfPos([pos[0]+1,pos[1]])][2]:
                            cleared.append([pos[0]+1,pos[1]+1])
            return cleared
    #We check if we can castle king side.
    def castleK(self,pos):
        cleared = []
        try:
            if not self.hasMoved \
                and not self.inCheck() \
                and not self.hasMovedRook1 \
                and self[self.getIndexOfPos[pos[0]+3,pos[1]]][1] == 'rook':
                if [pos[0]+1,pos[1]] in self.getChecked() \
                    or [pos[0]+2,pos[1]] in self.getChecked() \
                    or [pos[0]+3,pos[1]] in self.getChecked() \
                    or [pos[0]+1,pos[1]] in self.occupied \
                    or [pos[0]+2,pos[1]] in self.occupied:
                    return []
                cleared.append([pos[0]+2,pos[1]])
        except Exception as e:
            pass
        return cleared
    #We check if we can castle queen side.
    def castleQ(self,pos):
        cleared = []
        try:
            if not self.hasMoved \
                and not self.inCheck() \
                and not self.hasMovedRook0 \
                and self[self.getIndexOfPos[pos[0]+4,pos[1]]][1] == 'rook':
                if [pos[0]-1,pos[1]] in self.getChecked() \
                    or [pos[0]-2,pos[1]] in self.getChecked() \
                    or [pos[0]-4,pos[1]] in self.getChecked() \
                    or [pos[0]-1,pos[1]] in self.occupied \
                    or [pos[0]-2,pos[1]] in self.occupied:
                    return []
                cleared.append([pos[0]-2,pos[1]])
        except Exception as e:
            pass
        return cleared
    #The queening menu renderer.
    def renderMenu(self):
        if self.menu[0]:
            startPos = [self.menu[1][0]*width/11,self.menu[1][1]*height/11+1.5*height/11]
            tint(255,200)
            image(self.pieces["knight"],startPos[0],startPos[1])
            image(self.pieces["bishop"],startPos[0]+width/11,startPos[1])
            image(self.pieces["rook"],startPos[0]+2*width/11,startPos[1])
            image(self.pieces["queen"],startPos[0]+3*width/11,startPos[1])
            noFill()
            stroke(0)
            strokeWeight(1)
            if isInside(startPos[0],width/11,startPos[1],height/11):
                rect(startPos[0],startPos[1],width/11,height/11)
            if isInside(startPos[0]+width/11,width/11,startPos[1],height/11):
                rect(startPos[0]+width/11,startPos[1],width/11,height/11)
            if isInside(startPos[0]+2*width/11,width/11,startPos[1],height/11):
                rect(startPos[0]+2*width/11,startPos[1],width/11,height/11)
            if isInside(startPos[0]+3*width/11,width/11,startPos[1],height/11):
                rect(startPos[0]+3*width/11,startPos[1],width/11,height/11)
            strokeWeight(1)
            tint(255,255)
#The variable system.    
class Variable():
    def __init__(self,value):
        self.var = value
#We draw the board.    
def drawBoard():
    for x in xrange(8):
        for y in xrange(8):
            if (y%2 and not x%2 or not y%2 and x%2):
                fill(255)
                rect(x*width/11+1.5*width/11,y*height/11+1.5*height/11,
                     width/11,height/11)
#We check if the mouse is inside a box.           
def isInside(Xa,Xb,Ya,Yb):
    if Xa <= mouseX <= Xa+Xb and Ya <= mouseY <= Ya+Yb:
        return True
    return False
def rev(s):
     s = list(s)
     b = copy(s)
     for i in range(len(s)):
             s[i] = b[-1-i]
     return s
#The game loop.    
def draw():
    #We play around with the coords relative to the board.
    coords = [-1,-1]
    if width-width*1.5/11 > mouseX > width*1.5/11 \
        and height-height*1.5/11 > mouseY > height*1.5/11:
        if not WHITE.flip:
            coords=[int((mouseX-width*1.5/11)/(width/11)),
                    int((mouseY-height*1.5/11)/(height/11))]
        else:
            coords=[7-int((mouseX-width*1.5/11)/(width/11)),
                    7-int((mouseY-height*1.5/11)/(height/11))]
    if mousePressed:
        if not isPressed.var:
            isPressed.var = True
            if not WHITE.menu[0] and not BLACK.menu[0]:
                if WHITE.turn:
                    if WHITE.getIndexOfPos(coords) != None:
                        if View.var[1] != coords:
                            View.var[0] = True
                            View.var[1] = coords
                        else:
                            View.var[0] = False
                            View.var[1] = [-1,-1]
                    else:
                        if View.var[1] != None:
                            WHITE.setLegal(WHITE[WHITE.getIndexOfPos(View.var[1])])
                            if coords in WHITE.legal:
                                BLACK.update(coords,View)
                        View.var = [False,None]
                elif BLACK.turn:
                    if BLACK.getIndexOfPos(coords) != None:
                        if View.var[1] != coords:
                            View.var[0] = True
                            View.var[1] = coords
                        else:
                            View.var[0] = False
                            View.var[1] = [-1,-1]
                    else:
                        if View.var[1] != None:
                            BLACK.setLegal(BLACK[BLACK.getIndexOfPos(View.var[1])])
                            if coords in BLACK.legal:
                                WHITE.update(coords,View)
                        View.var = [False,None]    
            elif WHITE.menu[0]:
                startPos = [WHITE.menu[1][0]*width/11,WHITE.menu[1][1]*height/11+1.5*height/11]
                if isInside(startPos[0],width/11,startPos[1],height/11):
                    WHITE[WHITE.getIndexOfPos(WHITE.menu[1])][1] = "knight"
                    WHITE.menu[0] = False 
                    BLACK.flip = False
                    WHITE.flip = True
                if isInside(startPos[0]+width/11,width/11,startPos[1],height/11):
                    WHITE[WHITE.getIndexOfPos(WHITE.menu[1])][1] = "bishop"
                    WHITE.menu[0] = False 
                    BLACK.flip = False
                    WHITE.flip = True
                if isInside(startPos[0]+2*width/11,width/11,startPos[1],height/11):
                    WHITE[WHITE.getIndexOfPos(WHITE.menu[1])][1] = "rook"
                    WHITE.menu[0] = False 
                    BLACK.flip = False
                    WHITE.flip = True
                if isInside(startPos[0]+3*width/11,width/11,startPos[1],height/11):
                    WHITE[WHITE.getIndexOfPos(WHITE.menu[1])][1] = "queen"
                    WHITE.menu[0] = False 
                    BLACK.flip = False
                    WHITE.flip = True
            elif BLACK.menu[0]:
                startPos = [BLACK.menu[1][0]*width/11,BLACK.menu[1][1]*height/11+1.5*height/11]      
                if isInside(startPos[0],width/11,startPos[1],height/11):
                    BLACK[BLACK.getIndexOfPos(BLACK.menu[1])][1] = "knight"
                    BLACK.menu[0] = False 
                    BLACK.flip = True
                    WHITE.flip = False
                if isInside(startPos[0]+width/11,width/11,startPos[1],height/11):
                    BLACK[BLACK.getIndexOfPos(BLACK.menu[1])][1] = "bishop"
                    BLACK.menu[0] = False 
                    BLACK.flip = True
                    WHITE.flip = False
                if isInside(startPos[0]+2*width/11,width/11,startPos[1],height/11):
                    BLACK[BLACK.getIndexOfPos(BLACK.menu[1])][1] = "rook"
                    BLACK.menu[0] = False 
                    BLACK.flip = True
                    WHITE.flip = False
                if isInside(startPos[0]+3*width/11,width/11,startPos[1],height/11):
                    BLACK[BLACK.getIndexOfPos(BLACK.menu[1])][1] = "queen"
                    BLACK.menu[0] = False   
                    BLACK.flip = True
                    WHITE.flip = False
    else:
        isPressed.var = False
    background(89)
    if not WHITE.menu[0] and not BLACK.menu[0]:
        if View.var[0] and WHITE.turn:
            WHITE.setLegal(WHITE[WHITE.getIndexOfPos(View.var[1])])
        elif WHITE.getIndexOfPos(coords) != None and WHITE.turn:
            WHITE.setLegal(WHITE[WHITE.getIndexOfPos(coords)])
        else:
            WHITE.legal = []
        if View.var[0] and BLACK.turn:
            BLACK.setLegal(BLACK[BLACK.getIndexOfPos(View.var[1])])
        elif BLACK.getIndexOfPos(coords) != None and BLACK.turn:
            BLACK.setLegal(BLACK[BLACK.getIndexOfPos(coords)])
        else:
            BLACK.legal = []
    drawBoard()
    #We render the white and black pieces.
    WHITE.render()
    BLACK.render()
    #We fill everything in.
    fill(255)
    noStroke()
    rect(0,0,width,height*1.5/11)
    rect(width-width*1.5/11,0,width*1.5/11,height)
    rect(0,height-height*1.5/11,width,height*1.5/11)
    rect(0,0,width*1.5/11,height)
    stroke(50)
    strokeWeight(5)
    noFill()
    rect(width*1.5/11-2.5,height*1.5/11-2.5,width*8/11+5,height*8/11+5)
    strokeWeight(1)
    fill(0)
    textAlign(CENTER)
    letters = "abcdefgh"
    let = "87654321"
    if WHITE.flip:
        letters = rev(letters)
        let = rev(let)
    textSize(8)
    for i in range(8):
        text(letters[i],width*2/11+width*i/11,1.2*height/11)
        text(letters[i],width*2/11+width*i/11,height-height/11)
    for i in range(8):
        textAlign(RIGHT)
        text(let[i],width*1.5/11-width/44,height*2/11+height*i/11+height/88)
        textAlign(LEFT)
        text(let[i],width-width*1.5/11+width/44,height*2/11+height*i/11+height/88)
    textAlign(CENTER)
    #We call the menu renderer.
    WHITE.renderMenu()
    BLACK.renderMenu()
    textSize(20)
    fill(0)
    #We add the chess thing.
    text("Chess",width/2,height*1.2/11-height/22)
