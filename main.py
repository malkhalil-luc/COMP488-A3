import pygame

from src.game import Game

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Week 1 Intro Arcade (Pygame)")

    game = Game()
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(game.fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
