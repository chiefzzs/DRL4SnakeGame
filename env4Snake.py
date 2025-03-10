#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
import pygame
import sys
from pygame.locals import *
import numpy as np
from Agent import AgentDiscretePPO
import torch
from PIL import Image
from torchvision import transforms

class Snake:
    def __init__(self):
        self.snake_speed = 100 # 贪吃蛇的速度
        self.windows_width = 600
        self.windows_height = 600  # 游戏窗口的大小
        self.windows_width1 = self.windows_width+200
        self.cell_size = 50  # 贪吃蛇身体方块大小,注意身体大小必须能被窗口长宽整除
        self.map_width = int(self.windows_width / self.cell_size)
        self.map_height = int(self.windows_height / self.cell_size)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = (230, 230, 230)
        self.dark_gray = (40, 40, 40)
        self.DARKGreen = (0, 155, 0)
        self.Green = (0, 255, 0)
        self.Red = (255, 0, 0)
        self.blue = (0, 0, 255)
        self.dark_blue = (0, 0, 139)
        self.BG_COLOR = self.white  # 游戏背景颜色
        # 定义方向
        self.UP = 0
        self.DOWN = 1
        self.LEFT = 2
        self.RIGHT = 3

        self.HEAD = 0  # 贪吃蛇头部下标

        pygame.init()  # 模块初始化
        self.snake_speed_clock = pygame.time.Clock()  # 创建Pygame时钟对象

        [self.snake_coords,self.direction,self.food,self.state] = [None,None,None,None]

    def reset(self):
        '''
          初始化为水平的三个格子，向右移动，食物随机
        '''
        startx = random.randint(3, self.map_width - 8)  # 开始位置
        starty = random.randint(3, self.map_height - 8)
        self.snake_coords = [{'x': startx, 'y': starty},  # 初始贪吃蛇
                        {'x': startx - 1, 'y': starty},
                        {'x': startx - 2, 'y': starty}]
        self.direction = self.RIGHT  # 开始时向右移动
        self.food = self.get_random_location()  # 实物随机位置
        return self.getState()

    def step(self,action):
        '''
            强化学习输出的action ，进行贪食蛇行动
        '''
        if action == self.LEFT and self.direction != self.RIGHT:
            self.direction = self.LEFT
        elif action == self.RIGHT and self.direction != self.LEFT:
            self.direction = self.RIGHT
        elif action == self.UP and self.direction != self.DOWN:
            self.direction = self.UP
        elif action == self.DOWN and self.direction != self.UP:
            self.direction = self.DOWN
        # 移动
        self.move_snake(self.direction,self.snake_coords)
        # 检查是否活在
        ret = self.snake_is_alive(self.snake_coords)

        d = True if not ret else False
        # 检查是否吃到食物
        flag = self.snake_is_eat_food(self.snake_coords, self.food)
        # 奖励函数
        reward = self.getReward(flag,d)
        #self.getState() 返回状态给强化学习模型当做输入
        return [self.getState(),reward,d,None]

    def getReward(self,flag, d):
        '''
            本步骤奖励， 吃到食物+2 ，死亡 -0.5            
        '''
        reward = 0
        if flag:
            reward += 2
        # [xhead,yhead] = [self.snake_coords[self.HEAD]['x'],self.snake_coords[self.HEAD]['y']]
        # [xfood,yfood] = [self.food['x'],self.food['y']]
        # distance1 = np.sqrt((xhead-xfood)**2+(yhead-yfood)**2)
        # if distance1 < 1:
        #     reward += (1-distance1)/1
        if d: reward -= 0.5
        return reward


    def render(self):
        self.screen = pygame.display.set_mode((self.windows_width1, self.windows_height))
        self.screen.fill(self.BG_COLOR)
        self.draw_snake(self.screen,self.snake_coords)
        self.draw_food(self.screen,self.food)
        self.draw_score(self.screen,len(self.snake_coords)-3)
        pygame.display.update()
        self.snake_speed_clock.tick(self.snake_speed) #控制fps

    def getState(self):
        # 基础部分 6个维度

        # 食物到头的距离2个维度
        [xhead, yhead] = [self.snake_coords[self.HEAD]['x'], self.snake_coords[self.HEAD]['y']]
        [xfood, yfood] = [self.food['x'], self.food['y']]
        deltax = (xfood - xhead) / self.map_width
        deltay = (yfood - yhead) / self.map_height

        # 头上下左右点
        checkPoint = [[xhead,yhead-1],[xhead-1,yhead],[xhead,yhead+1],[xhead+1,yhead]]

        tem = [0,0,0,0]

        # 身体是否在头上下左右点上，如果是，记录
        for coord in self.snake_coords[1:]:
            if [coord['x'],coord['y']] in checkPoint:
                index = checkPoint.index([coord['x'],coord['y']])
                tem[index] = 1

        #如果头上下左右点在墙壁上，则记录
        for i,point in enumerate(checkPoint):
            if point[0]>=self.map_width or point[0]<0 or point[1]>=self.map_height or point[1]<0:
                tem[i] = 1

        state = [deltax,deltay]
        state.extend(tem)

        # 加入蛇身体中部和尾部位置信息  增加4个维度
        # length = len(self.snake_coords)
        # snake_mid = [self.snake_coords[int(length/2)]['x']-xhead,self.snake_coords[int(length/2)]['y']-yhead]
        # snake_tail = [self.snake_coords[-1]['x']-xhead,self.snake_coords[-1]['y']-yhead]
        # state.extend(snake_mid+snake_tail)
        return state

    def draw_food(self,screen, food):
        x = food['x'] * self.cell_size
        y = food['y'] * self.cell_size
        appleRect = pygame.Rect(x, y, self.cell_size, self.cell_size)
        pygame.draw.rect(screen, self.Red, appleRect)

    def draw_snake1(self, snake_coords):
        data = np.zeros((self.map_width,self.map_height))
        food = self.food
        data[food['x'],food['y']] = -1
        index=1
        for i,coord in enumerate(snake_coords):
            color = 1 if i == 0 else 2
            if( color ==1 ):
                data[coord['x']][coord['y']]  = color
            else:    
                data[coord['x']][coord['y']]  = index
            index+=1
        print(data)
        pass 
    
    # 将贪吃蛇画出来
    def draw_snake(self,screen, snake_coords):
        self.draw_snake1(snake_coords)
        for i,coord in enumerate(snake_coords):
            color = self.Green if i == 0 else self.dark_blue
            x = coord['x'] * self.cell_size
            y = coord['y'] * self.cell_size
            wormSegmentRect = pygame.Rect(x, y, self.cell_size, self.cell_size)
            pygame.draw.rect(screen, self.dark_blue, wormSegmentRect)
            wormInnerSegmentRect = pygame.Rect(  # 蛇身子里面的第二层亮绿色
                x + 4, y + 4, self.cell_size - 8, self.cell_size - 8)
            pygame.draw.rect(screen, color, wormInnerSegmentRect)

    # 移动贪吃蛇
    def move_snake(self,direction, snake_coords):
        if direction == self.UP:
            newHead = {'x': snake_coords[self.HEAD]['x'], 'y': snake_coords[self.HEAD]['y'] - 1}
        elif direction == self.DOWN:
            newHead = {'x': snake_coords[self.HEAD]['x'], 'y': snake_coords[self.HEAD]['y'] + 1}
        elif direction == self.LEFT:
            newHead = {'x': snake_coords[self.HEAD]['x'] - 1, 'y': snake_coords[self.HEAD]['y']}
        elif direction == self.RIGHT:
            newHead = {'x': snake_coords[self.HEAD]['x'] + 1, 'y': snake_coords[self.HEAD]['y']}
        else:
            newHead = None
            raise Exception('error for direction!')

        snake_coords.insert(0, newHead)

    # 判断蛇死了没
    def snake_is_alive(self,snake_coords):
        tag = True
        if snake_coords[self.HEAD]['x'] == -1 or snake_coords[self.HEAD]['x'] == self.map_width or snake_coords[self.HEAD]['y'] == -1 or \
                snake_coords[self.HEAD]['y'] == self.map_height:
            tag = False  # 蛇碰壁啦
        for snake_body in snake_coords[1:]:
            if snake_body['x'] == snake_coords[self.HEAD]['x'] and snake_body['y'] == snake_coords[self.HEAD]['y']:
                tag = False  # 蛇碰到自己身体啦
        return tag

    # 判断贪吃蛇是否吃到食物
    def snake_is_eat_food(self,snake_coords, food):  # 如果是列表或字典，那么函数内修改参数内容，就会影响到函数体外的对象。
        flag = False
        if snake_coords[self.HEAD]['x'] == food['x'] and snake_coords[self.HEAD]['y'] == food['y']:
            
            # 生成不重复位置的食物
            while True:
                food['x'] = random.randint(0, self.map_width - 1)
                food['y'] = random.randint(0, self.map_height - 1)  # 实物位置重新设置
                tag = 0
                for coord in snake_coords:
                    if [coord['x'],coord['y']] == [food['x'],food['y']]:
                        tag = 1
                        break
                if tag == 1: continue
                break
            flag = True
        else:
            del snake_coords[-1]  # 如果没有吃到实物, 就向前移动, 那么尾部一格删掉
        return flag

    # 食物随机生成
    def get_random_location(self):
        return {'x': random.randint(0, self.map_width - 1), 'y': random.randint(0, self.map_height - 1)}

    #打印字符串
    def draw_str(self,screen, msg ):
        font = pygame.font.Font('myfont.ttf', 30)
        scoreSurf = font.render(msg, True, self.black)
        scoreRect = scoreSurf.get_rect()
        scoreRect.topleft = (self.windows_width1 - 120, self.top)
        screen.blit(scoreSurf, scoreRect)
        self.top+=50
                
        
    # 画成绩
    def draw_score(self,screen, score):
        self.top = 10       
        self.draw_str(screen,'总长度: %s' % self.map_height*self.map_width)
        self.draw_str(screen,'得分: %s' % score)
        if(self.snake_coords):
            self.draw_str(screen,'长度: %s' % len(self.snake_coords))
         
 

    @staticmethod
    # 程序终止
    def terminate():
        pygame.quit()
        sys.exit()

    def screenTensor(self):
        self.render()
        image_data = pygame.surfarray.array3d(pygame.display.get_surface()).transpose((1,0,2))
        img = Image.fromarray(image_data.astype(np.uint8))
        # img = img.convert('1')
        transform = transforms.Compose([
                                        transforms.Resize((50, 50)),  # 只能对PIL图片进行裁剪
                                        transforms.ToTensor(),
                                        ])
        img_tensor = transform(img)
        # new_img_PIL = transforms.ToPILImage()(img_tensor).convert('RGB')
        # new_img_PIL.show()  # 处理后的PIL图片

        return img_tensor


if __name__ == "__main__":
    random.seed(100)
    env = Snake()
    env.snake_speed = 10
    agent = AgentDiscretePPO()
    # 初始化： 网络维度， 状态维度（强化学习的输入数据） ，动作维度（强化学习的输出数据维度）
    agent.init(512,6,4)
    agent.act.load_state_dict(torch.load('act_weight.pkl' , map_location=torch.device('cpu')))

    for _ in range(15):
        o = env.reset()
        # for _ in range(500):
        while 1:
            env.render()
            for event in pygame.event.get(): # 不加这句render要卡，不清楚原因
                pass
            # 依据o决定当做action
            a,_ = agent.select_action(o)
            o2,r,d,_ = env.step(a)
            o = o2
            if d:  
                print("please  press anykey ,q is exit")                      
                a= input()
                if(a == 'q'):
                    exit
                break


