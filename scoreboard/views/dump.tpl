<!DOCTYPE html>
<html>
<head>
<title>Game Dump</title>
</head>

<body>
  CHAINBOT INTERNAL GAME IDENTIFIER # <br>
  {{internal_id}} <br>

  RECORDED GAME # <br>
  {{user_game_id}} <br>

PLAYER LIST
<table>
  <tr>
    <th> ID </th>
    <th> NAME </th>
    <th> SCORE </th>
  </tr>
  %for player_num in sorted(list(player_data.keys())):
  %pnum = str(int(player_num)+1)
    <tr>
      <td> {{pnum}} </td>
      <td> {{player_data[player_num]['display_name']}} </td>
      <td> {{player_data[player_num]['score']}} </td>
    </tr>
  %end
</table>

EVENT LIST
<table>
  <tr>
    <th> EVENT </th>
    <th> TIME </th>
    <th> PLAYER </th>
    <th> INFO </th>
  </tr>
  %game_end_evt = None
  %for event in event_list:
  %gtime = event['evt_desc']['gtime']
  %evt_time = '{:02}:{:02}'.format(int(gtime/60), int(gtime%60))
  %if 'player' in event['evt_desc']:
  %pnum = event['evt_desc']['player']
  <tr>
    <td> {{event['evt_type']}} </td>
    <td> {{evt_time}} </td>
    <td> {{player_data[str(pnum)]['display_name']}} </td>
    <td> {{evt_info_gen(event)}} </td>
  </tr>
  %elif event['evt_type'] == 'GAME_END':
  %game_end_evt = event
  <tr>
    <td> GAME END </td>
    <td> {{evt_time}} </td>
    <td> - </td>
    <td> {{evt_info_gen(event)}} </td>
  </tr>
  %end
  %end
</table>

%if game_end_evt is not None:
REMAINING TIME AT END <br>
%rtime = game_end_evt['evt_desc']['rtime']
{{'{:02}:{:02}'.format(int(rtime/60), int(rtime%60))}}
%end
</body>
