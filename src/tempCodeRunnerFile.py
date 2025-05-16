for ship in game_state.multiplayer.player2_ships:
    #     ship_image = ship_images.get(ship['name'].lower())
    #     if ship_image:
    #         scaled_image = pygame.transform.scale(ship_image, (int(cell_size_p2 * ship['size']), int(cell_size_p2)))
    #         if ship['horizontal']:
    #             screen.blit(scaled_image, (player2_x + ship['col'] * cell_size_p2, player2_y + ship['row'] * cell_size_p2))
    #         else:
    #             rotated_image = pygame.transform.rotate(scaled_image, 90)
    #             screen.blit(rotated_image, (player2_x + ship['col'] * cell_size_p2, player2_y + ship['row'] * cell_size_p2))