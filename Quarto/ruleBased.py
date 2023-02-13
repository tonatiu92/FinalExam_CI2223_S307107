import quarto
import random
import numpy as np
import ast
from collections import defaultdict

class RuleBased(quarto.Player):
    def __init__(self, quarto: quarto.Quarto,params1: float = 0.12077208930524375, params2: float = 0.47262121794293277) -> None:
        super().__init__(quarto)
        self.params1 = params1
        self.params2 = params2
        self._status = None
    
    def choose_piece(self) -> int:
        return self.choosing_strategy()
    
    def place_piece(self) -> tuple[int, int]:
        return self.placing_strategy()
    
    def placing_strategy(self) -> tuple[int,int]:
        """
        Description: Placing a piece on the board

        @returns 
        tuple (i,j): the position where to place the piece
        """
        board_copy = self.get_game().get_board_status()
        completing = self.completing_raw(board_copy)
        if completing != [-1,-1]:
            return completing
        else:
            block = self.block_opponent(board_copy)
            if block != [-1,-1]:
                return block
            elif self.params1 != 0:
                if random.random() > self.params1:
                    region = self.scoring_strategy(board_copy)
                else:
                    region = self.scoring_strategy(board_copy, True)
                if region != [-1,-1]:
                    return region
                return self.oriented_random()
            else:
                """
                Naive Rule based
                """
                return random.randint(0, 3), random.randint(0, 3)
    
    #region Analysis
    def score_alignement(self, alignement: list, selected_piece_char: quarto.Piece, defense: bool = False) -> list:
        """
        Description: calculate the score for aligned pieces
        
        @args:
        alignement [list]: the list of pieces aligned
        selected_piece_char [quarto.Piece]: the piece to compare in order to get the score
        
        @returns:
        the list of score for each characteristics
        """
        score_char = [0,0,0,0] #HIGH, COLOURED, SOLID, SQUARE
        features = [[piece.HIGH, piece.COLOURED, piece.SOLID, piece.SQUARE] for piece in alignement] #Get the features of each piece
        selected_value  = [selected_piece_char.HIGH, selected_piece_char.COLOURED, selected_piece_char.SOLID, selected_piece_char.SQUARE]
        if not defense:
            """
            If we are going to make an offensive move
            """
            for i in range(4):
                count_feature = set([piece[i] for piece in features]) #get the feature n° i
                if ((len(count_feature) == 1) and (list(count_feature)[0] == selected_value[i])) :
                    score_char[i] = len(alignement)
        else:
            """
            If we are going to make a defensive
            """
            for i in range(4):
                count_feature = set([piece[i] for piece in features]) #get the feature n° i
                if ((len(count_feature) == 1) and (list(count_feature)[0] != selected_value[i])) :
                    score_char[i] = len(alignement)
        return score_char
    
    def board_analysis(self,piece_selected: int, defense: bool = False) -> dict:
        """
        Description: Calculate the score for each possible alignment
        
        @args
        piece_selected [int]: index of the piece selected to be insert on the board
        
        @returns
        The score for each possible alignement
        """
        board_copy = self.get_game().get_board_status()
        piece_selected = self.get_game().get_piece_charachteristics(piece_selected)
        horizontal = {"0":[],"1":[],"2":[],"3":[]}
        vertical = {"0":[],"1":[],"2":[],"3":[]}
        diag = {"0":[],"1":[]}        
        for i in range(self.get_game().BOARD_SIDE):
            for j in range(self.get_game().BOARD_SIDE):
                if board_copy[i,j] != -1:
                    piece = self.get_game().get_piece_charachteristics(board_copy[i,j])
                    horizontal[str(i)].append(piece)
                    vertical[str(j)].append(piece)
                    if i == j:
                        diag["0"].append(piece)
                    elif i + j == 3:
                        diag["1"].append(piece)
        scores = {"scoreH": {"0":[],"1":[],"2":[],"3":[]},"scoreV":{"0":[],"1":[],"2":[],"3":[]},"scoreD":{"0":[],"1":[]}}
        for k in range(self.get_game().BOARD_SIDE):
            scores["scoreH"][str(k)] = self.score_alignement(horizontal[str(k)],piece_selected, defense) 
            scores["scoreV"][str(k)] = self.score_alignement(vertical[str(k)],piece_selected, defense)
            if k <= 1:
                scores["scoreD"][str(k)] = self.score_alignement(diag[str(k)],piece_selected, defense)
        return scores

    def possible_quarto(self, board_copy: np.ndarray, scores: dict) -> tuple[int,int]:
        """
        Description: Analyze if there is a position candidate to make a quarto
        
        @args:
        board_copy [np.ndarray]: state of the board
        scores [dict]: scores of the alignement
        """
        for i in range(self.get_game().BOARD_SIDE):
            for j in range(self.get_game().BOARD_SIDE):
                if board_copy[i,j] == -1:
                    scoreH = scores["scoreH"][str(i)]
                    scoreV = scores["scoreV"][str(j)]
                    if i==j:
                        scoreD = scores["scoreD"]["0"]
                    elif i +j == 3:
                        scoreD = scores["scoreD"]["1"]
                    else:
                        scoreD = [0]
                    if 3 in scoreH or 3 in scoreV or 3 in scoreD:
                        return [j,i]
        return [-1,-1]             
        
    #endregion
    
    #region Placing Action 
    def completing_raw(self, board_copy:np.ndarray) -> tuple[int, int]:
        """
        TYPE OF STRATEGY:  ATTACK (critical action => Priority 1)
        DESCRIPTION: If there is an open space on the board where placing a piece would create a row of four pieces that all have a similarity,
        then place a piece of that similarity in that space.
        @returns: tuple[int, int]
        """
        scores = self.board_analysis(self.get_game().get_selected_piece())
        return self.possible_quarto(board_copy,scores)
    
    def block_opponent(self, board_copy: np.ndarray) -> tuple[int, int]:
        """
        TYPE OF STRATEGY: DEFENSE (critical action => Priority 1)
        DESCRIPTION: if there are no open spaces on the board where placing a piece would allow you to create a row of four pieces that share a common attribute, 
        then place a piece in a space where it is least likely to help your opponent create such a row.
        
        @returns: tuple[int, int]
        """
        for not_selected_pieces in range(self.get_game().NB_PIECES):
            if (not_selected_pieces != self.get_game().get_selected_piece())&(not_selected_pieces not in board_copy):
                scores = self.board_analysis(not_selected_pieces)
                position = self.possible_quarto(board_copy, scores)
                if position != [-1,-1]:
                    return position
        return [-1,-1]
    
    def oriented_random(self) -> tuple[int, int]:
        """
        TYPE OF STRATEGY: ATTACK
        DESCRIPTION: At the beginning of the game, it could be interesting to play on the diagonal where the possibility of quarto is 3 lines
        
        @returns: tuple[int, int]
        """
        l=[]
        length = self.get_game().BOARD_SIDE
        for i in range(length):
            if self.get_game().get_board_status()[i,i] == -1:
                l.append((i,i))
            if self.get_game().get_board_status()[length-1-i,i] == -1:
                l.append((i,length-1-i))
        if len(l) > 0:
            choose = random.randint(0,len(l)-1)
            return l[choose]
        else:
            return random.randint(0,3),random.randint(0,3)
    
    def scoring_positions(self, board_copy:np.ndarray, selected_piece: int, defense:bool = False):
        pos = []
        scores = self.board_analysis(selected_piece, defense)
        for i in range(self.get_game().BOARD_SIDE):
            for j in range(self.get_game().BOARD_SIDE):
                if board_copy[i,j] == -1:
                    scoreH = scores["scoreH"][str(i)]
                    scoreV = scores["scoreV"][str(j)]
                    if i==j:
                        scoreD = scores["scoreD"]["0"]
                    elif i+j ==3:
                        scoreD = scores["scoreD"]["1"]
                    else:
                        scoreD = [0]
                    total_score = sum(scoreH) + sum(scoreV) + sum(scoreD)*1000
                    if total_score == 0:
                        pos.append(((i,j),-1000))
                    else:
                        pos.append(((i,j),total_score))
        return pos

    def alignement(self, board_copy:np.ndarray, selected_piece: int, defense: bool = False) -> list:

       # returns: the possible horizontal, vertical, diagonal alignements

        board_score = sorted(self.scoring_positions(board_copy,selected_piece, defense), key=lambda x: x[1], reverse = True)
        horizontal = []
        vertical = []
        diagonal = []
        if len(board_score)<2:
            return horizontal, vertical, diagonal
        points_occurences = {} #dict to identify the points with many alignements type (max 3).

        #Looking for possible alignement
        for p1 in board_score:
            for p2 in board_score:
                #if the piece are not antagonist there are not a possible alignement
                if (p1!=p2) & (board_copy[p1[0][0],p1[0][1]] + board_copy[p2[0][0],p2[0][1]] != 15):
                   
                    #HorizontalCheck
                    if (p1[0][0] == p2[0][0]) & (((p2[0],p1[0]),p1[1] + p2[1]) not in horizontal):
                        
                        #adding alignement and penalizing some 
                        horizontal.append(((p1[0],p2[0]),p1[1] + p2[1]))
                        
                        #identifying points & penalizing some
                        if (str(p1[0]) not in points_occurences):
                            points_occurences[str(p1[0])] = 1
                        else:
                            points_occurences[str(p1[0])] += 1
                    
                    #VerticalCheck
                    if (p1[0][1] == p2[0][1]) & (((p2[0],p1[0]),p1[1] + p2[1]) not in vertical):
                        vertical.append(((p1[0],p2[0]),p1[1] + p2[1]))
                        
                        #identifying points
                        if str(p1[0]) not in points_occurences:
                            points_occurences[str(p1[0])] = 1
                        else:
                            points_occurences[str(p1[0])] += 1
                            
                    #DiagonalCheck
                    if (p1[0][0] == p1[0][1]) & (p2[0][0] == p2[0][1]) & (((p2[0],p1[0]),p1[1] + p2[1]) not in diagonal):
                        diagonal.append(((p1[0],p2[0]),p1[1] + p2[1]))
                        #identifying points
                        if str(p1[0]) not in points_occurences:
                            points_occurences[str(p1[0])] = 1
                        else:
                            points_occurences[str(p1[0])] += 1
                            
                    elif (p1[0][0] + p1[0][1] == 3) & (p2[0][0] + p2[0][1]== 3) & (((p2[0],p1[0]),p1[1] + p2[1]) not in diagonal):
                        diagonal.append(((p1[0],p2[0]),p1[1] + p2[1]))
                        
                        #identifying points
                        if str(p1[0]) not in points_occurences:
                            points_occurences[str(p1[0])] = 1
                        else:
                            points_occurences[str(p1[0])] += 1
        
        #rewards to points with more than 1 alignement
        for points in points_occurences.items():
            if points[1] >= 3:
                for el in horizontal:
                    if el[0] == ast.literal_eval(points[0]):
                        el[1] *= 10000
                for el in vertical:
                    if el[0] == ast.literal_eval(points[0]):
                        el[1] *= 10000
                for el in diagonal:
                    if el[0] == ast.literal_eval(points[0]):
                        el[1] *= 10000
                        
            elif points[1] >= 2:
                for el in horizontal:
                    if el[0] == ast.literal_eval(points[0]):
                        el[1] *= 1000
                for el in vertical:
                    if el[0] == ast.literal_eval(points[0]):
                        el[1] *= 1000
                for el in diagonal:
                    if el[0] == ast.literal_eval(points[0]):
                        el[1] *= 1000
          
        #Sorting according the sum of scores
        horizontal = sorted(horizontal, key=lambda x: x[1], reverse = True)
        vertical = sorted(vertical, key=lambda x: x[1], reverse = True)
        diagonal = sorted(diagonal, key=lambda x: x[1], reverse = True)

        return horizontal, vertical, diagonal
    
    def best_alignement(self, horizontal: list, vertical: list, diagonal: list) -> list:

        #Here we are trying to find the best alignement, when there is negative value of an alignement, we want to check if it is not the only one
        #because we don't to consider as good alignement negative one
    
        
        best_horizontal = ((-1,-1),-1)
        best_vertical = ((-1,-1),-1)
        best_diagonal = ((-1,-1),-1)
        if horizontal:  
            if horizontal[-1][1] < 0:
                for row in horizontal[:-1]:
                    if (row[0][0] != horizontal[-1][0][0]):
                        best_horizontal = row
            else:
                best_horizontal = horizontal[0]
        if vertical:
            if vertical[-1][1] < 0:
                for col in vertical[:-1]:
                    if (col[0][0] != vertical[-1][0][0]):
                        best_vertical = col
            else:
                best_vertical = vertical[0]
        
        if diagonal:
            if diagonal[-1][1] < 0:
                for diag in diagonal[:-1]:
                    if (diag[0][0] != diagonal[-1][0][0]):
                        best_diagonal = diag
            else:
                best_diagonal = diagonal[0]
        return best_horizontal, best_vertical, best_diagonal
     
    def choose_position(self,board_copy:np.ndarray, best_horizontal: list, best_vertical:list,best_diagonal:list):
        choice = None
        max_score = 0
        if (best_horizontal != ((-1,-1),-1)) | (best_vertical != ((-1,-1),-1)) | (best_diagonal != ((-1,-1),-1)):
            max_score = max([best_horizontal[1],best_vertical[1],best_diagonal[1]])
            if max_score > 0:
                if max_score == best_diagonal[1]:
                    if best_diagonal[0][0][0] == best_diagonal[0][0][1]:
                        t = [(i,j) for i in range(4) for j in range(4) if ((i==j)&(board_copy[i,j]==-1))]
                        if t:
                            choice = t[0]
                    else:
                        t = [(j,i) for i in range(4) for j in range(4) if ((i+j==3)&(board_copy[i,4-i-1]==-1))]
                        if t:
                            choice = t[0]
                            
                elif (max_score == best_horizontal[1]) & (choice is None):
                    t = [(j,best_horizontal[0][0][0]) for j in range(4) if (board_copy[best_horizontal[0][0][0],j]==-1)]
                    if t:
                        choice = t[0]
                        
                elif (max_score == best_vertical[1]) & (choice is None):
                    t = [(best_vertical[0][0][1],i) for i in range(4) if (board_copy[i,best_vertical[0][0][1]]==-1)]
                    if t:
                        choice = t[0]
            
                if choice:
                    return choice
                else:
                    return [-1,-1]
        return [-1,-1]      
        
    def scoring_strategy(self, board_copy:np.ndarray, defense = False)->tuple[int, int]:
        """
        TYPE OF STRATEGY: ATTACK
        DESCRIPTION: In this function we are trying to calculate the square where we are more likely to do a quarto win
        We already think the case of three pieces sharing a common attribute with the completing method
        Here we will try to find when 2 pieces are alignated
        
        @returns: tuple [int, int] 
        """
        selected_piece = self.get_game().get_selected_piece()
        horizontal, vertical, diagonal = self.alignement(board_copy, selected_piece, defense)
        best_horizontal, best_vertical, best_diagonal = self.best_alignement(horizontal, vertical, diagonal)
        return self.choose_position(board_copy,best_horizontal, best_vertical, best_diagonal) 
    
    #endregion
        
    #region Choosing Action according to Board Status
    def choosing_strategy(self):
        board_copy = self.get_game().get_board_status()
        index = self.giving_wrong_piece(board_copy)
        if index != -1:
            return index
        else:
            if self.params2 != 0:
                if random.random() >= self.params2:
                    index = self.most_present_in_bag(board_copy)
                else:
                    index = self.giving_wrong_piece_alignement(board_copy)
            
            if index != -1:
                return index
            else:
                return random.randint(0,15)
            
    def count_characteristics(self,bag:dict):
        characteristics = {"high":0, "small":0, "color": 0, "not_color":0, "solid": 0, "hollow": 0, "square":0,"round":0}
        for piece in bag:
            if bag[piece].HIGH:
                characteristics["high"] += 1
            else:
                characteristics["small"] += 1
            if bag[piece].COLOURED:
                characteristics["color"] += 1
            else:
                characteristics["not_color"] += 1
            if bag[piece].SOLID:
                characteristics["solid"] += 1
            else:
                characteristics["hollow"] += 1
            if bag[piece].SQUARE:
                characteristics["square"] += 1
            else:
                characteristics["round"] += 1
                
        return sorted(characteristics.items(), key=lambda x: x[1],reverse = True)
   
    def get_bag_pieces(self, board_copy: np.ndarray):
        """
        Return pieces that are not already in the bag
        """
        bag = {}
        for i in range(self.get_game().NB_PIECES):
            if i not in board_copy:
                bag[i] = self.get_game().get_piece_charachteristics(i)
        return bag
   
    def possible_quarto_list(self, board_copy: np.ndarray, scores: dict) -> list:
        pos_quarto = []
        for i in range(self.get_game().BOARD_SIDE):
            for j in range(self.get_game().BOARD_SIDE):
                if board_copy[i,j] == -1:
                    scoreH = scores["scoreH"][str(i)]
                    scoreV = scores["scoreV"][str(j)]
                    if i==j:
                        scoreD = scores["scoreD"]["0"]
                    elif i +j == 3:
                        scoreD = scores["scoreD"]["1"]
                    else:
                        scoreD = [0]
                    if 3 in scoreH or 3 in scoreV or 3 in scoreD:
                        pos_quarto.append([i,j])
        if len(pos_quarto) >= 1:
            return pos_quarto
        else:
            return [-1,-1]
   
    def most_present_in_bag(self, board_copy: np.ndarray):
        """ 
        Choose a piece that is the most present in the bag because it means it is also the less present in tje board
        """
        bag = self.get_bag_pieces(board_copy)
        target =  dict(self.count_characteristics(bag))
        keys = list(target.keys())
        target[keys[0]] *= 1000
        target[keys[1]] *= 500
        target[keys[2]] *= 100
        target[keys[3]] *= 50
        target[keys[4]] *= 10
        target[keys[5]] *= 5
        target[keys[6]] *= 1
        target[keys[7]] *= 0.1
    #(attribut, quantité)
        pieces = {}
        for index in bag:
            score = 0
            if (bag[index].HIGH) & (target == "high"):
                score += 1 * target["high"]
            elif (not bag[index].HIGH) & (target == "small"):
                score += 1 * target["small"]
            if (bag[index].COLOURED) & (target == "color"):
                score += 1 * target["color"]
            elif (not bag[index].COLOURED) & (target == "not_color"):
                score += 1 * target["not_color"]
            if (bag[index].SOLID) & (target == "solid"):
                score += 1 * target["solid"]
            elif (not bag[index].SOLID) & (target == "hollow"):
                score += 1 * target["hollow"]
            if (bag[index].SQUARE) & (target == "square"):
                score += 1 * target["square"]
            elif (not bag[index].SQUARE) & (target == "round"):
                score += 1 * target["round"]
            pieces[index] = score
        return sorted(pieces.items(), key=lambda x: x[1],reverse = True)[0][0]
 
    def giving_wrong_piece(self,  board_copy: np.ndarray) -> int:
        """
        TYPE OF STRATEGY: DEFENSE (Critical action ==> Priority 1)
        DESCRIPTION: If a possible quarto is coming, give a piece that could not make a quarto
        """
        list_possible_quarto = []
        bag = self.get_bag_pieces(board_copy)
        bag_index = []
        for piece in bag:
            index = list(range(self.get_game().NB_PIECES)).index(piece)
            scores = self.board_analysis(piece)
            pos = self.possible_quarto_list(board_copy,scores)
            bag_index.append(index)
            for i in range(self.get_game().BOARD_SIDE):
                for j in range(self.get_game().BOARD_SIDE):
                    #self.get_game().set_selected_piece(index)
                    if  [i,j] in pos :
                        list_possible_quarto.append(index)
        wrong_list = list(set(bag_index)-set(list_possible_quarto))
        if (len(wrong_list) != 0)&(len(list_possible_quarto)!=0):
            return wrong_list[random.randint(0, len(wrong_list)-1)]
        return -1
    
    def add_not_quarto(self, board_copy:np.ndarray, lines: dict) -> int:
        """
        @args:
        lines: dictionary containing the list of index for each alignement type h,v,d
        """
        bag = self.get_bag_pieces(board_copy)
        bag_score = {}
        
        #initialize the score for each piece in the bag
        for k,v in bag.items():
            bag_score[k] = 0
                
        #transform each index in a Piece object
        pieces_by_align = {"h":[],"v":[],"d":[]}
        for k,v in lines.items():
            if v:
                for index in v:
                    pieces_by_align[k].append(self.get_game().get_piece_charachteristics(index))
       
        
        #evaluating which common attributes are most present in the alignement
        attributes = {"HIGH":list((None,0)),"COLOURED":list((None,0)),"SOLID":list((None,0)),"SQUARE":list((None,0))}
        for k,v in pieces_by_align.items():
            #Look each pieces in the alignment
            characteristics = {"HIGH":True,"COLOURED":True, "SOLID": True, "SQUARE":True}
            if not pieces_by_align[k]:
                characteristics = {}
            else:
                for piece in pieces_by_align[k]:
                    for piece2 in pieces_by_align[k]:
                        if piece != piece2:
                            if (piece.HIGH != piece2.HIGH) :
                                characteristics.pop("HIGH", None)
                            if (piece.COLOURED != piece2.COLOURED):
                                characteristics.pop("COLOURED", None)
                            if (piece.SOLID != piece2.SOLID):
                                characteristics.pop("SOLID", None)
                            if( piece.SQUARE != piece2.SQUARE):
                                characteristics.pop("SQUARE", None)
                for a,b in characteristics.items():
                    if (attributes[a][0] is None)&(pieces_by_align[k] != []):
                        attributes[a][0] = getattr(pieces_by_align[k][0],a)
                    attributes[a][1] += 1
        
        scores = dict(sorted(attributes.items(),key=lambda x: x[1][1], reverse=True ))
        
        #scoring each piece in the bag
        for attribute,score in scores.items():
            if score[1] != 0:
                for index,piece in bag.items():
                    if (attribute == "HIGH")&(piece.HIGH == score[0]):
                        bag_score[index] += 10 * score[1]
                    elif (attribute == "COLOURED")&(piece.COLOURED == score[0]):
                        bag_score[index] += 10 * score[1]
                    elif (attribute == "SOLID")&(piece.SOLID == score[0]):
                        bag_score[index] += 10 * score[1]
                    elif (attribute == "SQUARE")&(piece.SQUARE == score[0]):
                        bag_score[index] += 10 * score[1]
        
        bag_score = sorted(bag_score.items(),key=lambda x: x[1])#from the lowest score to the highest
        return bag_score[0]
    
    def share_attributes_pieces(self, board_copy: np.ndarray, p1: tuple[int, int], p2:tuple[int, int]):
        """return a score for a piece in the board compared to the chosen piece"""
        score = 0
        piece1 = self.get_game().get_piece_charachteristics(board_copy[p1[0],p1[1]])
        piece2 = self.get_game().get_piece_charachteristics(board_copy[p2[0],p2[1]])
        if piece1.HIGH == piece2.HIGH:
            score += 1
        if piece1.COLOURED == piece2.COLOURED:
            score += 1
        if piece1.SOLID == piece2.SOLID:
            score += 1
        if piece1.SQUARE == piece2.SQUARE:
            score += 1
        if score == 0:
            """if the score == 0, it means the piece is antagonist to the chosen one, so we will try to penalize this positions"""
            score = -1000
        return score
    
    def giving_wrong_piece_alignement(self,  board_copy: np.ndarray) -> int:
        """
        TYPE OF STRATEGY: DEFENSE
        DESCRIPTION: giving a piece that will not be able to be place in the best alignement
        """
        score = 0
        index = -1
        for i in range(self.get_game().BOARD_SIDE):
            for j in range(self.get_game().BOARD_SIDE):
                if board_copy[i,j] != -1:
                    score_ij = 0
                    pieces = {"h":[],"v":[],"d":[]}
                    ##Check the column
                    for a in range(self.get_game().BOARD_SIDE):
                        if (board_copy[i,a] != -1) & ((i,a)!=(i,j)):
                            scoring_alignement = self.share_attributes_pieces(board_copy,(i,j),(i,a))
                            score_ij += scoring_alignement
                            pieces["h"].append(board_copy[i,a])
                            pieces["h"].append(board_copy[i,j])
                    ##Check the column
                    for a in range(self.get_game().BOARD_SIDE):
                        if (board_copy[a,j] != -1) & ((a,j)!=(i,j)):
                            scoring_alignement = self.share_attributes_pieces(board_copy,(i,j),(i,a))
                            score_ij += scoring_alignement
                            pieces["v"].append(board_copy[a,j])
                            pieces["v"].append(board_copy[i,j])
                    ##Check the diagonal
                    if i == j:
                        for a in range(self.get_game().BOARD_SIDE):
                            if(board_copy[a,a] != -1)&((a,a) != (i,j)):
                                scoring_alignement = self.share_attributes_pieces(board_copy,(i,j),(i,a))
                                score_ij += scoring_alignement
                                pieces["d"].append(board_copy[a,a])
                                pieces["d"].append(board_copy[i,j])
                    elif i + j == 3:
                        for a in range(self.get_game().BOARD_SIDE):
                            if(board_copy[a, 3-a] != -1) &((a, 3-a)!=(i,j)):
                                scoring_alignement = self.share_attributes_pieces(board_copy,(i,j),(i,a))
                                score_ij += scoring_alignement
                                pieces["d"].append(board_copy[a, 3-a])
                                pieces["d"].append(board_copy[i,j])
                    if score_ij > score:
                        score = score_ij
                        index = self.add_not_quarto(board_copy, pieces)[0]
        return index
    
            
    #endregion          
                        
                        
                

                    
            
        
        


