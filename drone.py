import time, sys
import ps_drone
import cv2, cv
from pykoki import *
import time
import pygame
from thread import start_new_thread

koki = PyKoki()
drone = ps_drone.Drone()  # Start using drone

global x
global y

active = False


def init():
    global error_x
    error_x = 0.0
    global error_y
    error_y = 0.0
    global xlast
    xlast = 0.0
    global ylast
    ylast = 0.0

    drone.startup()  # Connects to drone and starts subprocesses
    drone.reset()  # Sets drone's status to good (
    # LEDs turn green when red)
    drone.useDemoMode(True)  # Just give me 15 basic dataset per second (is default anyway)
    drone.setConfigAllID()  # Go to multiconfiguration-mode
    drone.sdVideo()  # Choose lower resolution (hdVideo() for...well, guess it)
    drone.frontCam()  # Choose front view
    # drone.videoFPS(5)
    CDC = drone.ConfigDataCount
    while CDC == drone.ConfigDataCount:
        time.sleep(0.0001)  # Wait until it is done (after resync is done)
    drone.startVideo()
    drone.showVideo()
    start_new_thread(process_video, ())
    drone_manual_controller()
    # start_new_thread(drone_manual_controller, ())
    # Number of encoded videoframes


def start_automatic_control():
    time.sleep(3)
    process_video()


def drone_manual_controller():
    drone.printBlue(
        "Battery: " + str(drone.getBattery()[0]) + "%  " + str(drone.getBattery()[1]))  # Gives a battery-status

    pygame.init()
    W, H = 320, 240
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    running = True
    global active
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYUP:
                drone.hover()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    drone.reset()
                    running = False
                # takeoff / land
                elif event.key == pygame.K_RETURN:
                    drone.takeoff()
                elif event.key == pygame.K_SPACE:
                    drone.land()
                # emergency
                elif event.key == pygame.K_BACKSPACE:
                    drone.reset()
                # forward / backward
                elif event.key == pygame.K_w:
                    drone.moveForward()
                elif event.key == pygame.K_s:
                    drone.moveBackward()
                # left / right
                elif event.key == pygame.K_a:
                    drone.moveLeft()
                elif event.key == pygame.K_d:
                    drone.moveRight()
                # up / down
                elif event.key == pygame.K_UP:
                    drone.moveUp()
                elif event.key == pygame.K_DOWN:
                    drone.moveDown()
                elif event.key == pygame.K_e:
                    drone.turnRight()
                elif event.key == pygame.K_q:
                    drone.turnLeft()
                elif event.key == pygame.K_1:
                    active = True
                elif event.key == pygame.K_2:
                    active = False
        try:
            surface = pygame.image.fromstring(drone.image, (W, H), 'RGB')
            # battery status
            hud_color = (255, 0, 0) if drone.navdata.get('drone_state', dict()).get('emergency_mask', 1) else (
                10, 10, 255)
            bat = drone.navdata.get(0, dict()).get('battery', 0)
            f = pygame.font.Font(None, 20)
            hud = f.render('Battery: %i%%' % bat, True, hud_color)
            screen.blit(surface, (0, 0))
            screen.blit(hud, (10, 10))
        except:
            pass

        pygame.display.flip()
        clock.tick(50)
        pygame.display.set_caption("FPS: %.2f" % clock.get_fps())

    print "Shutting down...",
    drone.shutdown()
    print "Ok."


def process_video():
    global x
    IMC = drone.VideoImageCount
    tlast = time.time()
    duration = 200
    print "start_video"
    while True:
        dt = tlast - time.time()
        tlast = time.time()
        while drone.VideoImageCount == IMC:
            time.sleep(0.01)  # Wait until the next video-frame    img = drone.VideoImage
        time.sleep(duration * 0.001)
        img1 = drone.VideoImage
        # print koki.find_markers(img, 0.1, params)
        #
        cv2.imwrite("test.jpg", img1)

        img = cv.LoadImage("test.jpg", cv.CV_LOAD_IMAGE_GRAYSCALE)
        params = CameraParams(Point2Df(img.width / 2, img.height / 2),
                              Point2Df(571, 571),
                              Point2Di(img.width, img.height))
        marker = koki.find_markers(img, 0.1, params)  # # #
        if len(marker) > 0:
            print "picture x", (marker[0]).centre.image.x
            print "picture y", (marker[0]).centre.image.y
            x = (marker[0]).centre.image.x / img.width
            y = (marker[0]).centre.image.y / img.height
            drone_controller(x, y, dt)
        else:
            if active:
                drone.hover()


def drone_controller(x, y, dt):
    global error_x
    global error_y
    global xlast
    global ylast
    # const
    Kp = 2
    Ki = 2
    Kd = 2
    ## x axis
    error_x += (x - 0.5)
    error_y += (y - 0.5)
    print "error x ", (x - 0.5), " error y ", (x - 0.5)
    u_x = Kp * (x - 0.5) + Kd * ((xlast - x) / dt) # + Ki * error_x
    u_y = Kp * (y - 0.5) + Kd * ((ylast - y) / dt) # + Ki * error_y
    xlast = x
    ylast = x
    print "move in x:", u_x
    print "move in y:", u_y
    global active
    if active:
        print "active"
        move_x(u_x)
        move_y(u_y)


def move_x(dx):
    if dx < 0.0:
        print "turn left "
        drone.turnLeft()
        return
    if dx > 0.0:
        print "turn right"
        drone.turnRight()
        return


def move_y(y):
    if y < 0.0:
        print "moveUP"
        drone.moveUp()
        return
    if y > 0.0:
        print "moveDown"
        drone.moveDown()
        return


init()
