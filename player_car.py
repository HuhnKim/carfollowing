import pygame

class PlayerCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 100
        self.color = (200, 0, 0)  # 빨간색
        
        # 속도 관련 변수 (km/h)
        self.min_speed = 10
        self.max_speed = 180  # 최대 속도 증가 (150 → 180)
        self.speed = 60  # 초기 속도
        self.speed_change = 5  # 키 입력당 속도 변화량 크게 증가 (10 → 18)
        self.acceleration_factor = 2.5  # 가속 계수 크게 증가 (2.0 → 3.5)
        
        # 좌우 이동 관련 변수
        self.lateral_speed = 8  # 좌우 이동 속도 증가 (7 → 8)
        self.left_moving = False
        self.right_moving = False
        
        # 속도 변화 부드럽게 하기 위한 변수
        self.target_speed = self.speed
        self.speed_smoothing = 0.3  # 속도 변화 계수 감소 (0.8 → 0.3) - 더 부드러운 변화를 위해
        
        # 이징(easing) 관련 변수
        self.acceleration_progress = 0  # 현재 가속/감속 진행 상태 (0~1)
        self.acceleration_duration = 1.0  # 가속/감속 완료까지 걸리는 시간 (초)
        self.acceleration_timer = 0  # 가속/감속 진행 시간
        self.is_accelerating = False  # 가속/감속 진행 여부
        self.prev_target_speed = self.speed  # 이전 목표 속도
        
        # 연속 키 입력을 위한 타이머
        self.key_press_timer = {
            pygame.K_UP: 0,
            pygame.K_DOWN: 0
        }
        self.key_press_interval = 0.03  # 연속 입력 간격 감소 (0.05 → 0.03)
        
        # 브레이크 등 관련 변수
        self.brake_lights_on = False  # 브레이크 등 상태
        self.is_down_key_pressed = False  # 아래 방향키 누름 상태
    
    def update(self, road_left, road_right):
        """플레이어 차량 상태 업데이트"""
        # 좌우 이동
        if self.left_moving:
            self.move_left()
        if self.right_moving:
            self.move_right()
            
        # 연속 키 입력 처리
        for key in self.key_press_timer:
            if self.key_press_timer[key] > 0:
                self.key_press_timer[key] -= 1/60  # 60fps 기준
                if self.key_press_timer[key] <= 0:
                    self.key_press_timer[key] = self.key_press_interval
                    if key == pygame.K_UP:
                        self.accelerate()
                    elif key == pygame.K_DOWN:
                        self.decelerate()
            
        # 차선을 벗어나지 않도록 제한
        half_width = self.width // 2
        if self.x - half_width < road_left + 5:
            self.x = road_left + half_width + 5
        elif self.x + half_width > road_right - 5:
            self.x = road_right - half_width - 5
        
        # 이징(easing) 방식으로 속도 업데이트
        self.update_speed_with_easing()
            
        # 디버그 출력
        print(f"Target Speed: {self.target_speed:.1f}, Current Speed: {self.speed:.1f}")
    
    def update_speed_with_easing(self):
        """이징(easing) 방식으로 속도 업데이트"""
        # 목표 속도와 현재 속도가 다를 때만 처리
        if abs(self.speed - self.target_speed) > 0.5:
            
            # 새로운 목표 속도로 바뀌었다면 이징 과정 재시작
            if not self.is_accelerating or abs(self.target_speed - self.prev_target_speed) > 0.5:
                self.is_accelerating = True
                self.acceleration_timer = 0
                self.prev_target_speed = self.target_speed
                
                # 가속, 감속에 따라 다른 지속 시간 적용
                if self.target_speed > self.speed:
                    # 가속 - 속도 차이가 클수록 오래 걸림 (최소 0.5초 ~ 최대
                    speed_diff = abs(self.target_speed - self.speed)
                    speed_ratio = speed_diff / self.max_speed
                    self.acceleration_duration = max(0.5, min(2.0, 0.5 + speed_ratio * 1.5))
                else:
                    # 감속 - 속도 차이가 클수록 오래 걸림 (최소 0.3초 ~ 최대
                    speed_diff = abs(self.target_speed - self.speed)
                    speed_ratio = speed_diff / self.max_speed
                    self.acceleration_duration = max(0.3, min(1.5, 0.3 + speed_ratio * 1.2))
            
            # 이징 타이머 업데이트
            self.acceleration_timer += 1/60  # 60fps 기준
            
            # 진행 비율 계산 (0~1)
            progress = min(1.0, self.acceleration_timer / self.acceleration_duration)
            
            # 이징 함수 적용 (Cubic easing - 점진적 변화)
            if self.target_speed > self.speed:  # 가속
                eased_progress = self.ease_in_out_cubic(progress)
            else:  # 감속
                eased_progress = self.ease_in_out_quad(progress)
                
            # 이징된 속도 계산
            start_speed = self.speed
            speed_diff = self.target_speed - start_speed
            self.speed = start_speed + speed_diff * eased_progress
            
            # 이징 완료 확인
            if progress >= 1.0:
                self.is_accelerating = False
                self.speed = self.target_speed
        else:
            self.is_accelerating = False
            self.speed = self.target_speed
    
    def ease_in_out_cubic(self, t):
        """Cubic 이징 함수 (In/Out)"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def ease_in_out_quad(self, t):
        """Quadratic 이징 함수 (In/Out)"""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
            
    def move_left(self):
        """왼쪽으로 이동"""
        self.x -= self.lateral_speed
        
    def move_right(self):
        """오른쪽으로 이동"""
        self.x += self.lateral_speed
    
    def accelerate(self):
        """가속"""
        # 현재 속도에서 점점 더 빠르게 가속 (급격한 변화)
        acceleration = self.speed_change * (1 + (self.speed / self.max_speed) * self.acceleration_factor)
        
        # 낮은 속도에서는 더 빠르게 가속
        if self.speed < 80:
            acceleration *= 1.5
            
        self.target_speed = min(self.max_speed, self.target_speed + acceleration)
        print(f"Accelerating: Target speed = {self.target_speed:.1f} km/h")
    
    def decelerate(self):
        """감속"""
        # 현재 속도에서 점점 더 빠르게 감속 (급격한 변화)
        deceleration = self.speed_change * (1 + (1 - self.speed / self.max_speed) * self.acceleration_factor)
        
        # 높은 속도에서는 더 빠르게 감속
        if self.speed > 120:
            deceleration *= 1.5
            
        self.target_speed = max(self.min_speed, self.target_speed - deceleration)
        print(f"Decelerating: Target speed = {self.target_speed:.1f} km/h")
    
    def handle_event(self, event):
        """키 입력 이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.left_moving = True
            elif event.key == pygame.K_RIGHT:
                self.right_moving = True
            # 속도 변경을 즉시 적용 (키 이벤트에서 직접 처리)
            elif event.key == pygame.K_UP:
                self.accelerate()
                self.key_press_timer[pygame.K_UP] = self.key_press_interval
            elif event.key == pygame.K_DOWN:
                self.decelerate()
                self.key_press_timer[pygame.K_DOWN] = self.key_press_interval
                self.is_down_key_pressed = True  # 아래 방향키 누름 상태 설정
                self.brake_lights_on = True  # 브레이크 등 켜기
                
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.left_moving = False
            elif event.key == pygame.K_RIGHT:
                self.right_moving = False
            # 키 해제 시 타이머 중지
            elif event.key == pygame.K_UP:
                self.key_press_timer[pygame.K_UP] = 0
            elif event.key == pygame.K_DOWN:
                self.key_press_timer[pygame.K_DOWN] = 0
                self.is_down_key_pressed = False  # 아래 방향키 누름 상태 해제
                # 여기서는 브레이크 등을 끄지 않음 (감속 중일 때 계속 유지)
    
    def draw(self, screen):
        """플레이어 차량 그리기"""
        # 차체 그리기
        pygame.draw.rect(screen, self.color, 
                         (self.x - self.width // 2, self.y - self.height // 2, 
                          self.width, self.height))
        
        # 헤드라이트 그리기
        # 왼쪽 헤드라이트
        pygame.draw.rect(screen, (255, 255, 200),
                         (self.x - self.width // 2 + 5, self.y - self.height // 2 + 5,
                          15, 10))
        
        # 오른쪽 헤드라이트
        pygame.draw.rect(screen, (255, 255, 200),
                         (self.x + self.width // 2 - 20, self.y - self.height // 2 + 5,
                          15, 10))
        
        # 브레이크 등 그리기
        # 감속 중이거나 아래 방향키가 눌렸을 때 브레이크 등 켜기
        if self.target_speed < self.speed - 1 or self.is_down_key_pressed:
            self.brake_lights_on = True
        elif not self.is_down_key_pressed:
            # 감속도 아니고 아래 방향키도 눌리지 않았을 때만 브레이크 등 끄기
            self.brake_lights_on = False
            
        # 브레이크 등 그리기
        if self.brake_lights_on:
            # 왼쪽 브레이크등
            pygame.draw.rect(screen, (255, 0, 0),
                            (self.x - self.width // 2 + 5, self.y + self.height // 2 - 15,
                             15, 10))
            
            # 오른쪽 브레이크등
            pygame.draw.rect(screen, (255, 0, 0),
                            (self.x + self.width // 2 - 20, self.y + self.height // 2 - 15,
                             15, 10))
        
        # 속도를 차 앞에 표시
        speed_text = f"{int(self.speed)}"
        # pygame 내장 폰트 사용 (없으면 기본 폰트 사용)
        try:
            font = pygame.font.SysFont('Arial', 20, bold=True)
        except:
            font = pygame.font.Font(None, 20)
        
        # 속도 텍스트 렌더링
        text_surface = font.render(speed_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.x, self.y - self.height // 2 - 15))
        
        # 텍스트 배경 (가독성 향상)
        bg_rect = text_rect.inflate(10, 5)
        pygame.draw.rect(screen, (50, 50, 50, 180), bg_rect)
        pygame.draw.rect(screen, (200, 200, 200), bg_rect, 1)  # 테두리
        
        # 텍스트 그리기
        screen.blit(text_surface, text_rect)
        
        # 속도계 시각화 (차량 위에 표시)
        # speed_ratio = (self.speed - self.min_speed) / (self.max_speed - self.min_speed)
        # speed_bar_width = 50
        # speed_bar_height = 8
        # pygame.draw.rect(screen, (100, 100, 100),
        #                 (self.x - speed_bar_width // 2, self.y - self.height // 2 - 20,
        #                  speed_bar_width, speed_bar_height))
        # pygame.draw.rect(screen, (255, 255 * (1 - speed_ratio), 0),
        #                 (self.x - speed_bar_width // 2, self.y - self.height // 2 - 20,
        #                  int(speed_bar_width * speed_ratio), speed_bar_height))
        
        # 속도 변화 화살표 표시 (가속/감속 시각적 피드백)
        # arrow_size = 15
        # if self.target_speed > self.speed + 3:
        #     # 가속 화살표 (위쪽)
        #     pygame.draw.polygon(screen, (0, 255, 0), [
        #         (self.x, self.y - self.height // 2 - 30),
        #         (self.x - arrow_size // 2, self.y - self.height // 2 - 30 + arrow_size),
        #         (self.x + arrow_size // 2, self.y - self.height // 2 - 30 + arrow_size)
        #     ])
        # elif self.target_speed < self.speed - 3:
        #     # 감속 화살표 (아래쪽)
        #     pygame.draw.polygon(screen, (255, 0, 0), [
        #         (self.x, self.y - self.height // 2 - 30 + arrow_size),
        #         (self.x - arrow_size // 2, self.y - self.height // 2 - 30),
        #         (self.x + arrow_size // 2, self.y - self.height // 2 - 30)
            # ]) 