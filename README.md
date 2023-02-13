# The Quarto Game

## The Rules
1. The game is played on a 4x4 grid, with 16 pieces that each have four attributes: shape (square or circle), height (tall or short), color (red or blue), an solidity (solid or hollow)
2. At the start of the game, all 16 pieces are placed in a bag or box.
3. Players take turns drawing a piece from the bag or box and placing it on the board.
4. On their turn, player 1 choose the piece that their opponent will place on their next turn. Player 2 c places piece
    * Piece starts at (0,0)
    * Then, player can increase either X or Y by 1
5. The game continues until one player creates a row of four pieces that share a common attributes (such as all being the same color or shape), at which point that player wins the game
6. If all 16 pieces have been placed on the board and no player has won, the game is a draw.

## Agent Rule-based System
I choose to create a rule based System to play QUarto. First, we have two main actions: choose a piece for the next player and place a piece on the board. 
### Placing Action
As many strategy game, we got two type of actions for placing pieces on the board. It is possible to make an attack move or a defensive one.


#### Analysis
As a human, before any move, the agent need to analyze the board. That is why I implemented some functions to score the free positions on the board. 

To do it, I created two functions that score the alignment present in the board. Therefore, instead of scoring a specific case, I will score each row, column and diagonal where it is possible to make a quarto. In other word, we have four possible alignment horizontally and vertically and 2 possible diagonals. I implemented the function **boardanalysis**. Furthermore, I decided to score the game by common characteristics shared between the aligned pieces. The **scorealignement** calculate for each characteristics the number of piece of the alignment which share the same. If all pieces aligned share the same characteristics with the piece chosen by the opponent, we can give a score to the piece. Otherwise, the characteristic is discarded. 

#### Beginning of the game
At the beginning of the game, we don't know where to play, so we can force the player to play in the diagonal.

#### Attack
Attack consist of making a move in order to win. It involves to take a risk. Using an offensive strategy, the player will try to make a quarto finding the best alignment. 


**Critical Attack**:

First of all, I take in account a critical case that will be the priority number one for the agent. If there is any possibility to make a quarto while he is playing, he must place the piece on the board. That is why I created a method **completingraw** that will make a quarto according the result of the method method **possiblequarto** that look at the score results seen previously. If there is a score of 3 in any alignement, the agent can place the piece on the free position. 

**Attack Scoring**

The attack strategy in a general case, is to place the piece in the best position to win the game. To begin with, we sum all the score for each possible alignement in the board (4 horizontal, 4 vertical, 2 diagonal) as seen before. Knowing all those alignement, we can know score the free positions.

For each aligned piece, the agent sum previous calculated score. Moreover, some pieces are present in many alignements. In order, to know the region/alignement where it will be more probable to make a quarto, we can upgrade the score according the number of occurences of a piece in an alignement. Finally, we will extract the best horizontal, diagonal and vertical alignement. (cf 
**alignement()** function)

As the two diagonals are the positions where the probability of making a quarto are greater, we will try to prioritize the placement on diagonals. Then using the maxScore we return the best position if some alignement exist.

#### Defense

**Critical Defense**

By defending, we mean trying to prevent the opponent to win. As for attack, the agent need to act critically when the opponent is about to win without calculating many possibilities. If a possible quarto is on the quarto and the piece holded by the agent cannot win, therefore we need to block the opponent. Using the same methodology than before, we will block him.


**Defense Scoring**
The scoring Strategy is the same as before, nevertheless, instead of comparing if the alignment is equal to the selected piece, we can see where is the best alignment where it doesn't share any characteristics to prevent a good alignment


### Choosing Action

In the quarto game, the player choose the piece in the bag for the opponent. We can also implement some strategies to decrease the chance of winning of the opponent

#### Giving a wrong piece
This action has also a critical case. When the opponent can make a quarto, we will try to give him a piece that cannot do this quarto if possible. To that we will try to make the list of the position where it can be a quarto. And if it exists one we will "discard" it from the possible pieces to take inside the bag.

For the general case, we will score the position as for the placing action but in an other way. We will try to understand the sharing attributes for each piece and each alignment. Instead of looking the best free position, we will look at the highest pieces on the board. Then, we need to select in the bag, the piece that doesn't match with the best alignment. That is why, instead of scoring free position, the agent will score the piece in the bag according to those already in the boarder. In order to do that, we have 3 main functions. 

Throughout we look at each position on the board **givingwrongalignement()**, we will look the score of the pieces on the board according to their alignment . And with the list of score for this pieces we will compare them to the pieces inside the bag (**addnotquarto()**). Finally we will get the score of the piece that is less likely to make a quarto  if selected, or, in other word, the piece in the bag with the lowest score.

#### Giving a piece with the characteristic most present in the bag

Another strategy to give a piece to the opponent is more simple. We can only give a piece whith the characteristics most present in the bag. As if there is more pieces with this characteristics in the bag, it is less likely to make a quarto with this piece because they are not in the board.


## Evolving the Rules

In the previous section, we discussed about the rules implemented. Both actions own two type of strategy. As we don't know which one to use in a first moment, we can parameterize the use of this rules. 

I had give paraemeter in a sequential order to get the best restults: We want to know the best parameter value to decide:

- Placing Strategy: Attack or Defend
- Choosing Strategy: Most frequent characteristic in the bag or Worst piece to play

As seen for the Lab2, we will use a genetic algorithm to evolve this rules

### Individuals
In this case an individual or genome is a list of two float parameters.

### Fitness
The fitness is the number of wins of the individual over 2 kind of player as was mentioned by a reviewer in the Lab3 of NIM. As I want to train my algorithm over different level of difficulty, I created two players to train my individuals against. The first one is the one totally random provided by the teacher. The second one, is a naive version of my Rule based system. It try to win when there is a obvious solution, but he plays randomly otherwise.

### Cross-Over
We will perform a cross-over between the parameters of both parent.

### Mutation
We will perform a mutation on one of the two parameter, applying a random mutation on it

### Tournament
We will get the maximum fitness between two Individuals

### Evolved Rules

Individual(genome=[0.12077208930524375, 0.47262121794293277], fitness=0.677) final best 



