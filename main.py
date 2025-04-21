import pygame
from car_game import CarGame

def main():
    # 게임 초기화
    pygame.init()
    
    # 게임 객체 생성 및 실행
    game = CarGame()
    game.run()
    
    # 게임 종료
    pygame.quit()

if __name__ == "__main__":
    main() 