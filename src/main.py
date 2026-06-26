import pygame

from game import Game

if __name__ == "__main__":
    print("pygame version:", pygame.version.ver)
    game = Game()
    game.run()
