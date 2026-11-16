<?php
$page_title = "LIMS Media Dashboard";
require_once('functions.php');
require_once('config.php');
include("header.php");
$version = "250403.0";

function convertToHMS($seconds) {
  $hours = floor($seconds / 3600);
  $minutes = floor(($seconds % 3600) / 60);
  $seconds = $seconds % 60;
  return sprintf("%d:%02d:%02d", $hours, $minutes, $seconds);
}
$total_views = 0;
$total_engagements = 0;
$part_twitter_total_engagement = "";
$part_website_event_count = "";
$part_instagram_plays = "";
echo'<body>';
if (isset($_POST['delete']) && isset($_POST['media_id'])) {
    // User has confirmed the delete action, so delete the row from the database
    $media_id = $_POST['media_id'];
    $delete_stmt = $db->prepare("DELETE FROM media_output WHERE media_id = :media_id");
    $delete_stmt->bindParam(':media_id', $media_id);
    $delete_stmt->execute();
}
//getting the user info
$username = $_SESSION['username'];
$sql_user = "SELECT user_id FROM users WHERE username = :username";
$stmt_user = $db->prepare($sql_user);
$stmt_user->execute(['username' => $username]);
$user_id = $stmt_user->fetchColumn();
//getting the user config
$stmt_config = $db->prepare("SELECT * FROM users_config WHERE user_id = ?");
$stmt_config->execute([$user_id]);
$row = $stmt_config->fetch(PDO::FETCH_ASSOC);
$showColumnsJson = $row['show_columns'];
$showColumnsArray = json_decode($showColumnsJson, true);
$start_date = $row['start_date'];
$end_date = $row['end_date'];
if (!$end_date) {
  $end_date = date('Y-m-d');
}
if (!$start_date) {
  $start_date = '2010-01-01';
}
$stmt1 = $db->prepare("SELECT show_programs, show_types, show_authors FROM users_config WHERE user_id = ?");
$stmt1->execute([$user_id]);
$user = $stmt1->fetch(PDO::FETCH_ASSOC);
$show_programs_array = explode(',', str_replace(array('{','}', '"'), '', $user['show_programs']));
$program_conditions = '';
$show_blank_parts = 0;
if (!empty($show_programs_array)) {
  if (in_array('Blank', $show_programs_array)) {
    // Exclude Blank option
    $show_programs_array = array_diff($show_programs_array, ['Blank']);
    $show_blank_parts = 1;
    if (empty($show_programs_array)) {
      // All options were Blank, so show only null programs
      $program_conditions = "(media_program IS NULL OR media_program = '')";
    } else {
      $program_conditions = "(media_program IN ('" . implode("','", $show_programs_array) . "') OR media_program IS NULL OR media_program = '')";
    }
  } else {
    $program_conditions = "media_program IN ('" . implode("','", $show_programs_array) . "')";
  }
} else {
  $program_conditions = "media_program IS NULL OR media_program = ''";
}
$show_types_array = explode(',', str_replace(array('{','}', '"'), '', $user['show_types']));




$type_conditions = '';

if (!empty($show_types_array)) {
    if (in_array('Empty', $show_types_array)) {
        // Always include NULL or empty media types
        $empty_condition = "(media_type IS NULL OR media_type = '')";

        // Remove "Empty" from the array since we've already accounted for it
        $show_types_array = array_diff($show_types_array, ['Empty']);

        if (!empty($show_types_array)) {
            // Combine conditions to include both empty and non-empty selected types
            $type_conditions = "($empty_condition OR media_type IN ('" . implode("','", array_map('addslashes', $show_types_array)) . "'))";
        } else {
            // Only empty media types condition if no other types remain
            $type_conditions = $empty_condition;
        }
    } else {
        // Standard condition without "Empty" selected
        $type_conditions = "media_type IN ('" . implode("','", array_map('addslashes', $show_types_array)) . "')";
    }
} else {
    // If no filters are applied, show only empty media types
    $type_conditions = "(media_type IS NULL OR media_type = '')";
}






$show_authors_array = explode(',', str_replace(array('{','}', '"'), '', $user['show_authors']));
$authors_conditions = 'TRUE'; // Default condition (fetch all if no filter)

if (!empty($show_authors_array)) {
    $show_authors_array = array_map('trim', $show_authors_array); // Trim whitespace from names

    // Separate {empty} from actual author names
    $empty_authors = in_array('empty', $show_authors_array);
    $selected_authors = array_diff($show_authors_array, ['empty']);

    $conditions = [];

    if (!empty($selected_authors)) {
        // Create query condition to match media_id from media_authors table
        $quoted_authors = "'" . implode("','", $selected_authors) . "'";
        $conditions[] = "media_output.media_id IN (
            SELECT media_id FROM media_authors WHERE author_name IN ($quoted_authors)
        )";
    }

    // If {empty} is selected, include media_output rows that don't have an entry in media_authors
    if ($empty_authors) {
        $conditions[] = "media_output.media_id NOT IN (SELECT media_id FROM media_authors)";
    }

    if (!empty($conditions)) {
        // **Ensure parentheses around the OR condition to avoid overriding other filters**
        $authors_conditions = "(" . implode(" OR ", $conditions) . ")";
    }
}












// Get all existing programs
$stmt_programs = $db->prepare("
    SELECT DISTINCT media_program FROM media_programs WHERE media_program IS NOT NULL
");
$stmt_programs->execute();
$existing_programs = array_map(function($row) {
    return $row['media_program'];
}, $stmt_programs->fetchAll(PDO::FETCH_ASSOC));

// Get all existing types
$stmt_types = $db->prepare("
    SELECT DISTINCT media_type FROM media_types WHERE media_type IS NOT NULL
");
$stmt_types->execute();
$existing_types = array_map(function($row) {
    return $row['media_type'];
}, $stmt_types->fetchAll(PDO::FETCH_ASSOC));



$stmt = $db->prepare("
SELECT DISTINCT media_output.media_id, title, title_english, media_date, author, media_link, media_source_link, media_source, video_length, media_video_embed_link, media_youtube_link, media_facebook_link, media_facebook_views, media_facebook_likes, media_instagram_link, media_twitter_link, media_tiktok_link, media_whatsapp, youtube_date
FROM media_output
LEFT JOIN media_programs ON media_output.media_id = media_programs.media_id
LEFT JOIN media_types ON media_output.media_id = media_types.media_id
WHERE media_output.media_id IN (
    SELECT media_id FROM media_output WHERE media_date BETWEEN :start_date AND :end_date
)
AND $program_conditions
AND $type_conditions 
AND $authors_conditions
ORDER BY media_output.media_date DESC, media_output.media_id DESC
");




$stmt->bindParam(':start_date', $start_date);
$stmt->bindParam(':end_date', $end_date);
$stmt->execute();




echo "<div class='content'>";
// Add a link to create a new media output row
echo"   <div class='menu'>
        <p>
        <a href='edit.php' class='button'>Create Post</a>
        <a title='Get last 30 days posts from limslb.com website' href='get_posts4.php' class='button'>Get posts</a>
        <a href='export.php' class='button'>Export table</a>";
        echo"<a href='user_config.php' class='button'>User config</a>";
        if ($is_admin){
          echo"<a href='kpis_refresh.php' class='button'>Social media KPIS refresh</a>";
          echo"<a href='logs.php' class='button'>Logs</a>";
        }
   echo"</p></div>";
echo "<div class='table_div' id='table1'>";
echo "<table id='my-table'>";
echo "<thead><tr><th></th><th>#</th>";


if ($showColumnsArray['Title']) {echo "<th>Title</th>";}
if ($showColumnsArray['Title_english']) {echo "<th>English Title</th>";}
if ($showColumnsArray['Output']) {echo "<th>Output</th>";}
if ($showColumnsArray['Video_length']) {echo "<th>Video length</th>";}
if ($showColumnsArray['URL']) {echo "<th>Website link</th>";}

if ($showColumnsArray['KPIs']) {echo "<th>Website Views</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Website average duration</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Website total users</th>";}
if ($showColumnsArray['KPIs']) {echo "<th title='Engagement is calculated based on events count'>Website engagements</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Website engagement rate</th>";}

if ($showColumnsArray['Embedded_video_link']) {echo "<th>Embedded video link</th>";}
if ($showColumnsArray['Date']) {echo "<th>Date</th>";}
//if ($showColumnsArray['Author']) {echo "<th>Expert</th>";}
if ($showColumnsArray['Author']) {echo "<th>Expert</th>";}

if ($showColumnsArray['Original_link']) {echo "<th>Media</th>";}
if ($showColumnsArray['Original_link']) {echo "<th>Source link</th>";}

if ($showColumnsArray['KPIs']) {echo "<th title='Views in case the source link is youtube'>Source views (youtube)</th>";}
if ($showColumnsArray['KPIs']) {echo "<th title='Likes in case the source link is youtube'>Source likes (youtube)</th>";}
if ($showColumnsArray['KPIs']) {echo "<th title='Comments in case the source link is youtube'>Source comments (youtube)</th>";}



if ($showColumnsArray['Program']) {echo "<th>Program</th>";}
if ($showColumnsArray['Categories']) {echo "<th>Categories</th>";}
if ($showColumnsArray['Tags']) {echo "<th>Tags</th>";}
if ($showColumnsArray['Whatsapp_sent']) {echo "<th>Whatsapp sent</th>";}
if ($showColumnsArray['Youtube_link']) {echo "<th>Youtube link</th>";}
if ($showColumnsArray['Youtube_date']) {echo "<th>Youtube date</th>";}

if ($showColumnsArray['KPIs']) {echo "<th>Youtube Views</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Youtube Engagements</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Youtube Likes</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Youtube Comments</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Youtube Shares</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Youtube Card Clicks</th>";}

//if ($showColumnsArray['KPIs']) {echo "<th>Youtube Impressions</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Youtube Watch Time</th>";}

if ($showColumnsArray['Status']) {echo "<th>Status</th>";}
if ($showColumnsArray['Facebook_link']) {echo "<th>Facebook link</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>FB Views</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>FB Total engagements</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>FB Positive engagements</th>";}


/*if ($showColumnsArray['Facebook_likes']) {echo "<th>Facebook_likes</th>";}
if ($showColumnsArray['Facebook_views']) {echo "<th>Facebook_views</th>";}*/
if ($showColumnsArray['Instagram_link']) {echo "<th>Instagram link</th>";}
if ($showColumnsArray['KPIs']) {echo "<th title='Instagram views is the number of views for a picture and the number of plays for a video'>Instagram Views</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Instagram Engagements</th>";}


if ($showColumnsArray['Twitter_link']) {echo "<th>Twitter link</th>";}

//if ($showColumnsArray['KPIs']) {echo "<th>Twitter views</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Twitter likes</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Twitter retweets</th>";}
//if ($showColumnsArray['KPIs']) {echo "<th>Twitter replies</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Twitter impressions</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Twitter total engagement</th>";}



if ($showColumnsArray['Tiktok_link']) {echo "<th>Tiktok link</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Tiktok Views</th>";}
if ($showColumnsArray['KPIs']) {echo "<th>Tiktok Engagements</th>";}

if ($showColumnsArray['Copies_number']) {echo "<th>Copies</th>";}
if ($showColumnsArray['Edit']) {echo "<th>Edit</th>";}


if ($is_admin && isset($showColumnsArray['Delete']) && $showColumnsArray['Delete']) {
    echo "<th>Delete</th>";
}

echo "</tr></thead>";


echo "<tbody>";
// Loop through each row in the result set and add it to the HTML table
$row_num = 0;
$copies_count = 0;
$rowIndex = 0;
while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
  $row_num += 1;
    echo "<tr class='outer-row'>";
    $media_id = $row['media_id'];

    $source_youtube_views = "";
    $source_youtube_likes = "";
    $source_youtube_comments = "";

    $youtube_views = "";
    $youtube_likes = "";
    $youtube_comments = "";
    $youtube_shares = "";
    $youtube_card_clicks = "";

    //$youtube_impressions = "";
    $youtube_watch_time = "";

    $twitter_views = "";
    $twitter_likes = "";
    $twitter_retweets = "";
    $twitter_replies = "";
    $twitter_impressions = "";
    $twitter_total_engagement = "";

    $website_views = "";
    $website_duration = "";
    $website_total_users = "";
    $website_event_count = "";
    $website_engagement_rate = "";
    
    $tiktok_views = "";
    $tiktok_engagements = "";

    $instagram_plays = "";
    $instagram_engagements = "";

    $facebook_views = "";
    $facebook_comments = "";
    $facebook_shares = "";
    $facebook_like = "";
    $facebook_love = "";
    $facebook_haha = "";
    $facebook_wow = "";
    $facebook_sad = "";
    $facebook_angry = "";
    $facebook_engagements = "";
    $facebook_positive_engagements = "";
    $youtube_engagements = "";
    // Get YouTube, Twitter, and Website metrics (views, likes, comments, etc.) for the given media_id
    $stmt_metrics = $db->prepare("
        SELECT 
            youtube_views, youtube_likes, youtube_comments, youtube_shares, youtube_card_clicks, youtube_watch_time, source_youtube_views, source_youtube_likes, source_youtube_comments,
            twitter_views, twitter_likes, twitter_retweets, twitter_replies, twitter_impressions, twitter_total_engagement,
            website_views, website_duration, website_total_users, website_event_count, website_engagement_rate, tiktok_views, tiktok_engagements,
            instagram_plays, instagram_engagements, facebook_views, facebook_comments, facebook_shares, facebook_likes, facebook_love, facebook_haha, facebook_wow, facebook_sad, facebook_angry, facebook_link_clicks
        FROM media_kpis 
        WHERE media_id = :media_id
    ");
    $stmt_metrics->bindParam(':media_id', $media_id, PDO::PARAM_INT);
    $stmt_metrics->execute();
    $result = $stmt_metrics->fetch(PDO::FETCH_ASSOC);
    $facebook_engagements_tooltip = "";
    $facebook_positive_tooltip = "";
    $youtube_engagements_tooltip ="";
    if ($result !== false) {
        $youtube_views = $result['youtube_views'];
        $youtube_likes = $result['youtube_likes'];
        $youtube_comments = $result['youtube_comments'];
        $youtube_shares = $result['youtube_shares'];
        $youtube_card_clicks = $result['youtube_card_clicks'];
        
        $source_youtube_views = $result['source_youtube_views'];
        $source_youtube_likes = $result['source_youtube_likes'];
        $source_youtube_comments = $result['source_youtube_comments'];

        //$youtube_impressions = $result['youtube_impressions'];
        $youtube_watch_time = $result['youtube_watch_time'];
        if ($youtube_watch_time){$youtube_watch_time = convertToHMS($youtube_watch_time);}
        else {$youtube_watch_time = "";}
        $twitter_views = $result['twitter_views'];
        $twitter_likes = $result['twitter_likes'];
        $twitter_retweets = $result['twitter_retweets'];
        $twitter_replies = $result['twitter_replies'];
        $twitter_impressions = $result['twitter_impressions'];
        $twitter_total_engagement = $result['twitter_total_engagement'];

        $website_views = $result['website_views'];
        $website_duration = $result['website_duration'];
        $website_total_users = $result['website_total_users'];
        $website_event_count = $result['website_event_count'];
        $website_engagement_rate = $result['website_engagement_rate'];

        $tiktok_views = $result['tiktok_views'];
        $tiktok_engagements = $result['tiktok_engagements'];

        $instagram_plays = $result['instagram_plays'];
        $instagram_engagements = $result['instagram_engagements'];

        $facebook_views = $result['facebook_views'];
        $facebook_comments = $result['facebook_comments'];
        $facebook_shares = $result['facebook_shares'];
        $facebook_like = $result['facebook_likes'];
        $facebook_love = $result['facebook_love'];
        $facebook_haha = $result['facebook_haha'];
        $facebook_wow = $result['facebook_wow'];
        $facebook_sad = $result['facebook_sad'];
        $facebook_angry = $result['facebook_angry'];
        $facebook_link_clicks = $result['facebook_link_clicks'];

        $facebook_engagements_tooltip = "";
        $facebook_positive_tooltip = "";
        $youtube_engagements_tooltip = "";
        if ($facebook_views) {
          $facebook_engagements = $facebook_comments + $facebook_shares + $facebook_like + $facebook_love + $facebook_haha + $facebook_wow + $facebook_sad + $facebook_angry + $facebook_link_clicks;
          $facebook_positive_engagements = $facebook_comments + $facebook_shares + $facebook_like + $facebook_love + $facebook_haha + $facebook_wow + $facebook_link_clicks;
          $facebook_engagements_tooltip = "Comments: $facebook_comments\nShares: $facebook_shares\nLink clicks: $facebook_link_clicks\nLikes: $facebook_like\nLove: $facebook_love\nHaha: $facebook_haha\nWow: $facebook_wow\nSad: $facebook_sad\nAngry: $facebook_angry";
          $facebook_positive_tooltip = "Comments: $facebook_comments\nShares: $facebook_shares\nLikes: $facebook_like\nLove: $facebook_love\nHaha: $facebook_haha\nWow: $facebook_wow";
        
        }
        if ($youtube_views) {
          $youtube_engagements = $youtube_likes + $youtube_comments + $youtube_shares + $youtube_card_clicks;
          $youtube_engagements_tooltip = "Likes: $youtube_likes\nComments: $youtube_comments\nShares: $youtube_shares\nCard Clicks: $youtube_card_clicks";
        }
        if (!empty($website_duration)) {
          $website_duration = substr($website_duration, 0, 8); // Keep only HH:MM:SS
      }
    }
 

    $type_stmt = $db->prepare("SELECT string_agg(media_type, ', ') AS media_type FROM media_types WHERE media_id = :media_id");
    $type_stmt->bindParam(':media_id', $media_id);
    $type_stmt->execute();
    $type_row = $type_stmt->fetch(PDO::FETCH_ASSOC);  

    if ($showColumnsArray['Show_parts'] && (strpos($type_row['media_type'], 'TV Interview') !== false || strpos($type_row['media_type'], 'Radio Interview') !== false)) {
        echo "<td class='collapse-button' data-media-id='$media_id' style='font-size: 24px; line-height:24px;' title='Add Part'>+</td>";
    }
     else {echo "<td style='min-width: 15px;'></td>";}
    echo "<td>" . $row_num . "</td>"; 
    if ($showColumnsArray['Title']) {
      echo "<td style='width: 50px; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; direction: rtl;' class='editable' data-media-id='$media_id' data-field='title' title='" . $row['title'] . "'>" . $row['title'] . "</td>";
    }
    if ($showColumnsArray['Title_english']) {
      echo "<td style='max-width:100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable' data-media-id='$media_id' data-field='title_english' title='" . $row['title_english'] . "'>" . $row['title_english'] . "</td>";
    }
    if ($showColumnsArray['Output']) {
      $media_type_display = $type_row['media_type']; 
      // Check the media type and set the display value accordingly
      if ($media_type_display === 'TV Interview') {
          $media_type_display = 'Video';
      } elseif ($media_type_display === 'Radio Interview') {
          $media_type_display = 'Audio';
      } elseif ($media_type_display === 'News Website') {
          $media_type_display = 'Written';
      }  
      echo "<td style='min-width: 100px; max-width: 100px;'>" . $media_type_display . "</td>";
  }
    if ($showColumnsArray['Video_length']) {echo "<td style = 'width: 50px;'>" . $row['video_length'] . "</td>";}
    if ($showColumnsArray['URL']) {   echo "<td style = 'width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'><a href='" . $row['media_link'] . "' target='_blank'>" . $row['media_link'] . "</a></td>";}
    
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $website_views . "</td>";}
    $total_views += (int) $website_views;
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $website_duration . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $website_total_users . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $website_event_count . "</td>";}
    $total_engagements += (int) $website_event_count;
    //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $website_engagement_rate . "</td>";}

    
    if ($showColumnsArray['Embedded_video_link']) {   echo "<td style = 'width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'><a href='" . $row['media_video_embed_link'] . "' target='_blank'>" . $row['media_video_embed_link'] . "</a></td>";}
    if ($showColumnsArray['Date']) {  echo "<td style = 'width: 50px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>" . $row['media_date'] . "</td>";}
    //if ($showColumnsArray['Author']) {    echo "<td style = 'width: 60px;'>" . $row['author'] . "</td>";}
    //if ($showColumnsArray['Author']) {    echo "<td style = 'width: 60px;'>" . $row['author'] . "</td>";}
    if ($showColumnsArray['Author']) {
      $author_stmt = $db->prepare("SELECT string_agg(author_name, ', ') AS author_names FROM media_authors WHERE media_id = :media_id");
      $author_stmt->bindParam(':media_id', $media_id);
      $author_stmt->execute();
      $author_row = $author_stmt->fetch(PDO::FETCH_ASSOC);
      $author_names = htmlspecialchars($author_row['author_names'] ?? '');
  
      echo "<td style='width: 60px; cursor: pointer;' onclick='editAuthors($media_id)'>$author_names</td>";
  }
  
  
    
    if ($showColumnsArray['Original_link']) {    
      
      
      echo "<td style='width: 120px; max-width: 100px; white-space: nowrap; overflow: hidden; cursor:pointer;' 
      title='" . $row['media_source'] . "' 
      onclick='openPopup(" . $row['media_id'] . ", \"" . htmlspecialchars($row['media_source'], ENT_QUOTES) . "\")'>
      " . htmlspecialchars($row['media_source']) . "</td>";
      
      
      echo "<td style = 'width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'><a href='" . $row['media_source_link'] . "' target='_blank'>" . $row['media_source_link'] . "</a></td>";  
    }
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $source_youtube_views . "</td>";}
    $total_views += (int) $source_youtube_views;
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $source_youtube_likes . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $source_youtube_comments . "</td>";}
    $total_engagements += (int) $source_youtube_likes + (int) $source_youtube_comments;
    if ($showColumnsArray['Program']) {    
      // Query the media_programs to get the programs for this media_id
      $media_id = $row['media_id'];
      $program_stmt = $db->prepare("SELECT string_agg(media_program, ', ') AS media_program FROM media_programs WHERE media_id = :media_id");
      $program_stmt->bindParam(':media_id', $media_id);
      $program_stmt->execute();
      $program_row = $program_stmt->fetch(PDO::FETCH_ASSOC);
      echo "<td style = 'min-width: 170px; max-width: 220px;'>" . $program_row['media_program'] . "</td>";
    }
    if ($showColumnsArray['Categories']) {    
      // Query the media_categories and media_copies tables to get the programs and copies for this media_id
      $media_id = $row['media_id'];
      $category_stmt = $db->prepare("SELECT string_agg(media_category, ', ') AS media_category FROM media_categories WHERE media_id = :media_id");
      $category_stmt->bindParam(':media_id', $media_id);
      $category_stmt->execute();
      $category_row = $category_stmt->fetch(PDO::FETCH_ASSOC);
      echo "<td style = 'width: 50px; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title = '". $category_row['media_category'] ."'>" . $category_row['media_category'] . "</td>";
    }   
    if ($showColumnsArray['Tags']) {    
      // Query the media_tags and media_copies tables to get the programs and copies for this media_id
      $media_id = $row['media_id'];
      $tag_stmt = $db->prepare("SELECT string_agg(media_tag, ', ') AS media_tag FROM media_tags WHERE media_id = :media_id");
      $tag_stmt->bindParam(':media_id', $media_id);
      $tag_stmt->execute();
      $tag_row = $tag_stmt->fetch(PDO::FETCH_ASSOC);
      echo "<td style = 'width: 50px; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title = '". $tag_row['media_tag'] ."'>" . $tag_row['media_tag'] . "</td>"; 
    }
    if ($showColumnsArray['Whatsapp_sent']) {
      $checked = $row['media_whatsapp'] ? 'checked' : '';
      echo '<td><input type="checkbox" name="whatsapp_checkbox" ' . $checked . ' onchange="updateWhatsappStatus(this, ' . $media_id . ', \'media\')" /></td>';
    }    
    if ($showColumnsArray['Youtube_link']) {
      echo "<td style='width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable' data-media-id='$media_id' data-field='media_youtube_link' title='" . $row['media_youtube_link'] . "'><a href='{$row['media_youtube_link']}' target='_blank'>" . $row['media_youtube_link'] . "</a></td>";
  }
  if ($showColumnsArray['Youtube_date']) {
    echo "<td style = 'width: 50px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>" . $row['youtube_date'] . "</td>";
}




if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_views . "</td>";}
if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;' title='$youtube_engagements_tooltip'>" . $youtube_engagements . "</td>";}
$total_views += (int) $youtube_views;
$total_engagements += (int) $youtube_engagements;
//if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_likes . "</td>";}
//if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_comments . "</td>";}
//if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_shares . "</td>";}
//if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_card_clicks . "</td>";}

//if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_impressions . "</td>";}
if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $youtube_watch_time . "</td>";}





if ($showColumnsArray['Status']) {
  $youtubeLink = $row['media_youtube_link'];
  $media_id = $row['media_id']; // Ensure $media_id is defined
  $currentStatus = $db->query("SELECT media_lebanonmatters_status FROM media_output WHERE media_id = $media_id")->fetchColumn();

  // Check if the current status is 'NA' or 'reviewed', if so, skip the YouTube API check
  if ($currentStatus !== 'NA' && $currentStatus !== 'reviewed' && $currentStatus !== 'filled') {
    $description = get_youtube_description($media_id, 'media');
    $apiKey = 'AIzaSyBq-9LmXxQKWPeCmkUqaHFt7XWuM-cE9uk';
    $videoId = extract_video_id($youtubeLink);
    $apiUrl = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=$videoId&key=$apiKey";
    $response = file_get_contents($apiUrl);
    $data = json_decode($response, true);
    $channelTitle = $data['items'][0]['snippet']['channelTitle'] ?? '';

    if ($channelTitle === 'LebanonMatters' && $description === '' && $currentStatus !== 'filled' && $currentStatus !== 'reviewed') {
      // Update to "blank"
      $db->query("UPDATE media_output SET media_lebanonmatters_status = 'blank' WHERE media_id = $media_id");
      $currentStatus = 'blank';
    } elseif ($channelTitle === 'LebanonMatters' && $description !== '' && $currentStatus === 'blank') {
      // Update to "filled"
      $db->query("UPDATE media_output SET media_lebanonmatters_status = 'filled' WHERE media_id = $media_id");
      $currentStatus = 'filled';
    } else {
      // Update to "NA"
      $db->query("UPDATE media_output SET media_lebanonmatters_status = 'NA' WHERE media_id = $media_id");
      $currentStatus = 'NA';
    }
  }
  // Determine which radio button should be checked
  $status1Checked = $currentStatus === 'blank' ? 'checked' : '';
  $status2Checked = $currentStatus === 'filled' ? 'checked' : '';
  $status3Checked = $currentStatus === 'reviewed' ? 'checked' : '';

  $enableStatus3 = $currentStatus === 'filled' ? '' : 'disabled';
  $greenButtonStatus = $currentStatus === 'filled' ? 'filled' : '';
  if ($currentStatus !== 'NA'){
  echo "
  <td style='width: 50px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
    <input type='radio' name='status$rowIndex' id='blank_youtube_description_$rowIndex' value='blank_youtube_description' style='display: none;' $status1Checked disabled />
    <label for='blank_youtube_description_$rowIndex' class='radio-label' data-color='red' title='Blank LebanonMatters YouTube description'></label>

    <input type='radio' name='status$rowIndex' id='unreviewed_youtube_description_$rowIndex' value='unreviewed_youtube_description' style='display: none;' $status2Checked disabled />
    <label for='unreviewed_youtube_description_$rowIndex' class='radio-label' data-color='orange' title='LebanonMatters YouTube description filled but not reviewed yet'></label>

    <input type='radio' name='status$rowIndex' id='reviewed_youtube_description_$rowIndex' value='reviewed_youtube_description' style='display: none;' $status3Checked $enableStatus3 />
    <label for='reviewed_youtube_description_$rowIndex' class='radio-label active-radio' data-color='green' title='LebanonMatters YouTube description filled and reviewed'
           onclick='handleStatusClick(event, $media_id, \"$greenButtonStatus\")'></label>
  </td>";
  }
  else {
    echo "<td></td>";
  }
  $rowIndex++; // increment row index
}





    if ($showColumnsArray['Facebook_link']) {
      echo "<td style='width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable' data-media-id='$media_id' data-field='media_facebook_link' title='" . $row['media_facebook_link'] . "'><a href='{$row['media_facebook_link']}' target='_blank'>" . $row['media_facebook_link'] . "</a></td>";
    }
    
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $facebook_views . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;' title='$facebook_engagements_tooltip'>" . $facebook_engagements . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;' title='$facebook_positive_tooltip'>" . $facebook_positive_engagements . "</td>";}
    $total_views += (int) $facebook_views;
    $total_engagements += (int) $facebook_engagements;
    if ($showColumnsArray['Instagram_link']){echo "<td style='width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable' data-media-id='$media_id' data-field='media_instagram_link' title='" . $row['media_instagram_link'] . "'><a href='{$row['media_instagram_link']}' target='_blank'>" . $row['media_instagram_link'] . "</a></td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $instagram_plays . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $instagram_engagements . "</td>";}
    $total_views += (int) $instagram_plays;
    $total_engagements += (int) $instagram_engagements;
    
    if ($showColumnsArray['Twitter_link']) {echo "<td style='width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable' data-media-id='$media_id' data-field='media_twitter_link' title='" . $row['media_twitter_link'] . "'><a href='{$row['media_twitter_link']}' target='_blank'>" . $row['media_twitter_link'] . "</a></td>";}
    
    //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $twitter_views . "</td>";}
    //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $twitter_likes . "</td>";}
    //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $twitter_retweets . "</td>";}
    //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $twitter_replies . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $twitter_impressions . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $twitter_total_engagement . "</td>";}
    $total_views += (int) $twitter_impressions;
    $total_engagements += (int) $twitter_total_engagement;

    if ($showColumnsArray['Tiktok_link']) {echo "<td style='width: 50px; max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable' data-media-id='$media_id' data-field='media_tiktok_link' title='" . $row['media_tiktok_link'] . "'><a href='{$row['media_tiktok_link']}' target='_blank'>" . $row['media_tiktok_link'] . "</a></td>";}    
    
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $tiktok_views . "</td>";}
    if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $tiktok_engagements . "</td>";}
    $total_views += (int) $tiktok_views;
    $total_engagements += (int) $tiktok_engagements;
    
    
    //get the number of copies
    $media_id = $row['media_id'];
    $copies_stmt = $db->prepare("SELECT COUNT(copy_id) AS copies FROM media_copies WHERE media_id = :media_id");
    $copies_stmt->bindParam(':media_id', $media_id);
    $copies_stmt->execute();
    $copies_row = $copies_stmt->fetch(PDO::FETCH_ASSOC);
    $copies_count += $copies_row['copies'];
    if ($showColumnsArray['Copies_number']) {echo "<td>" . $copies_row['copies'] . "</td>";}
    if ($showColumnsArray['Edit']) {echo "<td><a href='edit.php?media_id=" . $row['media_id'] . "'>Edit</a></td>";}
    if ($is_admin && $showColumnsArray['Delete']) {echo "<td><a href='delete.php?media_id=" . $row['media_id'] . "' onclick='return confirm(\"Are you sure you want to delete this row?\")'>Delete</a></td>";}
    echo "</tr>";

    if ($showColumnsArray['Show_parts']) {
      if (strpos($type_row['media_type'], 'TV Interview') !== false || strpos($type_row['media_type'], 'Radio Interview') !== false) {
            echo "<td colspan='" . ($is_admin && $showColumnsArray['Delete'] ? 18 : 17) . "'>";
            $media_id = $row['media_id'];
            $parts_stmt = $db->prepare("SELECT * FROM media_parts WHERE media_id = :media_id ORDER BY part_id");
            $parts_stmt->bindParam(':media_id', $media_id);
            $parts_stmt->execute();
            $part_nb = 1;
            while ($part_row = $parts_stmt->fetch(PDO::FETCH_ASSOC)) {
                $part_id = $part_row['part_id'];
                // Prepare a SELECT query to retrieve programs based on part_id
                $stmt_select_programs = $db->prepare("SELECT part_program_name FROM parts_programs WHERE part_id = :part_id");
                $stmt_select_programs->bindParam(':part_id', $part_id);
                $stmt_select_programs->execute();   
                $part_programs_array = $stmt_select_programs->fetchAll(PDO::FETCH_COLUMN);
                $part_programs = implode(', ', $part_programs_array);   
                
                if (empty(array_intersect($show_programs_array, $part_programs_array)) && !($show_blank_parts)) {
                  continue;
                }

              $part_facebook_views = '';
              $part_facebook_engagements = '';
              $part_website_views = '';
              $part_website_engagements = '';
              $part_instagram_views = '';
              $part_instagram_engagements = '';
              $part_tiktok_views = '';
              $part_tiktok_engagements = '';
              $part_youtube_views = '';
              $part_youtube_engagements = '';
              $part_twitter_impressions = "";
              $part_twitter_engagements = "";

                if ($showColumnsArray['KPIs']){  
                  // SQL for parts kpis
                  $query_kpis_parts = "SELECT part_facebook_views, part_facebook_comments, part_facebook_shares, part_facebook_likes, 
                              part_facebook_love, part_facebook_haha, part_facebook_wow, part_facebook_sad, part_facebook_angry, part_facebook_link_clicks, part_instagram_plays, part_instagram_engagements,
                              part_tiktok_views, part_tiktok_engagements,
                              part_youtube_views, part_youtube_likes, part_youtube_comments, part_youtube_shares, part_youtube_card_clicks, part_youtube_watch_time,
                              part_website_views, part_website_duration, part_website_total_users, part_website_event_count, part_twitter_impressions, part_twitter_total_engagement 
                            FROM parts_kpis WHERE part_id = :part_id";

                  $stmt_kpis_part = $db->prepare($query_kpis_parts);
                  $stmt_kpis_part->bindParam(':part_id', $part_id, PDO::PARAM_INT);
                  $stmt_kpis_part->execute();
                  $part_kpis = $stmt_kpis_part->fetch(PDO::FETCH_ASSOC);
                  $part_twitter_impressions = "";
                  $part_twitter_engagements = "";
                  if ($part_kpis !== false) {
                    $part_facebook_views = $part_kpis['part_facebook_views'];
                    $part_facebook_comments = $part_kpis['part_facebook_comments'];
                    $part_facebook_shares = $part_kpis['part_facebook_shares'];
                    $part_facebook_likes = $part_kpis['part_facebook_likes'];
                    $part_facebook_love = $part_kpis['part_facebook_love'];
                    $part_facebook_haha = $part_kpis['part_facebook_haha'];
                    $part_facebook_wow = $part_kpis['part_facebook_wow'];
                    $part_facebook_sad = $part_kpis['part_facebook_sad'];
                    $part_facebook_angry = $part_kpis['part_facebook_angry'];
                    $part_facebook_link_clicks = $part_kpis['part_facebook_link_clicks'];

                    $part_instagram_plays = $part_kpis['part_instagram_plays'];
                    $part_instagram_engagements = $part_kpis['part_instagram_engagements'];

                    $part_tiktok_views = $part_kpis['part_tiktok_views'];
                    $part_tiktok_engagements = $part_kpis['part_tiktok_engagements'];
                    
                    $part_youtube_views = $part_kpis['part_youtube_views'];             
                    $part_youtube_likes = $part_kpis['part_youtube_likes'];
                    $part_youtube_comments = $part_kpis['part_youtube_comments'];
                    $part_youtube_shares = $part_kpis['part_youtube_shares'];
                    $part_youtube_card_clicks = $part_kpis['part_youtube_card_clicks'];
                    //$part_youtube_impressions = $part_kpis['part_youtube_impressions'];
                    $part_youtube_watch_time = $part_kpis['part_youtube_watch_time'];
                    if ($part_youtube_watch_time){$part_youtube_watch_time = convertToHMS($part_youtube_watch_time);}
                    else {$part_youtube_watch_time = "";}
                    $part_website_views = $part_kpis['part_website_views'];
                    $part_website_duration = $part_kpis['part_website_duration'] ;      
                    $part_website_total_users = $part_kpis['part_website_total_users'];
                    $part_website_event_count = $part_kpis['part_website_event_count'];

                    $part_twitter_impressions = $part_kpis['part_twitter_impressions'];
                    $part_twitter_total_engagement = $part_kpis['part_twitter_total_engagement'];
                    // Default tooltips
                    $part_facebook_engagements_tooltip = "";
                    $part_facebook_positive_tooltip = "";
                    $part_youtube_engagements = "";
                    $part_youtube_engagements_tooltip = "";
                    if ($part_youtube_views) {
                      $part_youtube_engagements = $part_youtube_comments + $part_youtube_likes + $part_youtube_shares + $part_youtube_card_clicks;
                      $part_youtube_engagements_tooltip =
                          "Likes: $part_youtube_likes\n" .
                          "Comments: $part_youtube_comments\n" .
                          "Shares: $part_youtube_shares\n" .
                          "Card clicks: $part_youtube_card_clicks\n";
                    } else {
                      // Default values if no views
                      $part_youtube_engagements = "";
                      $part_youtube_engagements_tooltip = "";
                  }
                    if ($part_facebook_views) {
                        $part_facebook_engagements = $part_facebook_comments + $part_facebook_shares + $part_facebook_likes + $part_facebook_love + $part_facebook_haha + $part_facebook_wow + $part_facebook_sad + $part_facebook_angry + $part_facebook_link_clicks;
                        $part_facebook_positive_engagements = $part_facebook_comments + $part_facebook_shares + $part_facebook_likes + $part_facebook_love + $part_facebook_haha + $part_facebook_wow + $part_facebook_link_clicks;
                    
                        $part_facebook_engagements_tooltip = 
                            "Comments: $part_facebook_comments\n" .
                            "Shares: $part_facebook_shares\n" .
                            "Link clicks: $part_facebook_link_clicks\n" .
                            "Likes: $part_facebook_likes\n" .
                            "Love: $part_facebook_love\n" .
                            "Haha: $part_facebook_haha\n" .
                            "Wow: $part_facebook_wow\n" .
                            "Sad: $part_facebook_sad\n" .
                            "Angry: $part_facebook_angry";
                    
                        $part_facebook_positive_tooltip = 
                            "Comments: $part_facebook_comments\n" .
                            "Shares: $part_facebook_shares\n" .
                            "Likes: $part_facebook_likes\n" .
                            "Love: $part_facebook_love\n" .
                            "Haha: $part_facebook_haha\n" .
                            "Wow: $part_facebook_wow";
                    } else {
                        // Default values if no views
                        $part_facebook_engagements = "";
                        $part_facebook_positive_engagements = "";
                    }
                  } else {
                      // Default values if no KPIs found
                      $part_facebook_views = "";
                      $part_facebook_comments = "";
                      $part_facebook_shares = "";
                      $part_facebook_likes = "";
                      $part_facebook_love = "";
                      $part_facebook_haha = "";
                      $part_facebook_wow = "";
                      $part_facebook_sad = "";
                      $part_facebook_angry = "";
                      $part_facebook_link_clicks = "";
                      $part_facebook_engagements = "";
                      $part_facebook_positive_engagements = "";
                      $part_facebook_engagements_tooltip = "";
                      $part_facebook_positive_tooltip = "";
                      $part_instagram_plays = "";
                      $part_instagram_engagements = "";
                      $part_tiktok_views = "";
                      $part_tiktok_engagements = "";
                      $part_youtube_views = "";             
                      $part_youtube_likes = "";
                      $part_youtube_comments = "";
                      $part_youtube_shares = "";
                      $part_youtube_card_clicks = "";

                      $part_youtube_engagements = "";
                      $part_youtube_engagements_tooltip = "";
                      //$part_youtube_impressions = "";
                      $part_youtube_watch_time = "";
                      $part_website_views = "";
                      $part_website_duration = "" ;      
                      $part_website_total_users = "";
                      $part_website_event_count = "";

                      $part_twitter_impressions = "";
                      $part_twitter_engagements = "";
                  }
                }

                echo "<tr class='inner-row'>";
                echo "<td></td>";
                echo "<td>p$part_nb</td>";
                $part_nb += 1;
                //if ($showColumnsArray['Title']){echo "<td style='direction: rtl; max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{$part_row['part_title']}'>{$part_row['part_title']}</td>";}
                if ($showColumnsArray['Title']) {echo "<td style='direction: rtl; text-align:right; max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' class='editable-part' data-part-id='$part_id' data-field='part_title' title='{$part_row['part_title']}'>{$part_row['part_title']}</td>";}
                if ($showColumnsArray['Title_english']){echo "<td></td>";}
                if ($showColumnsArray['Output']) {echo "<td></td>";}
                if ($showColumnsArray['Video_length']) {echo "<td>{$part_row['part_length']}</td>";}
                if ($showColumnsArray['URL']) {echo "<td><a href='{$part_row['part_website_link']}' target='_blank' title='{$part_row['part_website_link']}'>{$part_row['part_website_link']}</a></td>";}
                
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_website_views . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_website_duration . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_website_total_users . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_website_event_count . "</td>";}
                $total_engagements += (int) $part_website_event_count;
                $total_views += (int) $part_website_views;

                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                
                if ($showColumnsArray['Embedded_video_link']) {echo "<td></td>";}
                if ($showColumnsArray['Date']) {  echo "<td></td>";}
                //if ($showColumnsArray['Author']) {  echo "<td></td>";}
                if ($showColumnsArray['Author']) {  echo "<td></td>";}

                if ($showColumnsArray['Original_link']) {  echo "<td></td><td></td>";}  
                
                if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                if ($showColumnsArray['KPIs']) {echo "<td></td>";}

                if ($showColumnsArray['Program']) {echo "<td>{$part_programs}</td>";}
                if ($showColumnsArray['Categories']) {  echo "<td></td>";  }
                if ($showColumnsArray['Tags']) {   echo "<td></td>";} 
                if ($showColumnsArray['Whatsapp_sent']) {
                  $checked = $part_row['part_whatsapp'] ? 'checked' : '';
                  echo "<td><input type='checkbox' name='whatsapp_checkbox' $checked onchange='updateWhatsappStatus(this, " . $part_row['part_id'] . ", \"part\")'></td>";
                }
                if ($showColumnsArray['Youtube_link']) {echo "<td class='editable-part' data-part-id='$part_id' data-field='part_youtube_link'><a href='{$part_row['part_youtube_link']}' target='_blank'>{$part_row['part_youtube_link']}</a></td>";}
                if ($showColumnsArray['Youtube_date']) {echo "<td></td>";}
   

                

                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_youtube_views . "</td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_youtube_likes . "</td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_youtube_comments . "</td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;' title = '$part_youtube_engagements_tooltip'>" . $part_youtube_engagements . "</td>";}
                $total_views += (int) $part_youtube_views;
                $total_engagements += (int) $part_youtube_engagements;



                //if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_youtube_impressions . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_youtube_watch_time . "</td>";}

                if ($showColumnsArray['Status']) {echo "<td></td>";}
                if ($showColumnsArray['Facebook_link']) {echo "<td class='editable-part' data-part-id='$part_id' data-field='part_facebook_link'><a href='{$part_row['part_facebook_link']}' target='_blank'>{$part_row['part_facebook_link']}</a></td>";}
                
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_facebook_views . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;' title='$part_facebook_engagements_tooltip'>" . $part_facebook_engagements . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;' title='$part_facebook_positive_tooltip'>" . $part_facebook_positive_engagements . "</td>";}
                $total_views += (int) $part_facebook_views;
                $total_engagements += (int) $part_facebook_engagements;

                
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}

                /*if ($showColumnsArray['Facebook_views']) {echo "<td>{$part_row['part_facebook_views']}</td>";}
                if ($showColumnsArray['Facebook_likes']) {echo "<td>{$part_row['part_facebook_likes']}</td>";}
                */
                if ($showColumnsArray['Instagram_link']) {echo "<td class='editable-part' data-part-id='$part_id' data-field='part_instagram_link'><a href='{$part_row['part_instagram_link']}' target='_blank'>{$part_row['part_instagram_link']}</a></td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_instagram_plays . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_instagram_engagements . "</td>";}
                $total_views += (int) $part_instagram_plays;
                $total_engagements += (int) $part_instagram_engagements;

                

                
                if ($showColumnsArray['Twitter_link']) {echo "<td class='editable-part' data-part-id='$part_id' data-field='part_twitter_link'><a href='{$part_row['part_twitter_link']}' target='_blank'>{$part_row['part_twitter_link']}</a></td>";}
                
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";} //views likes comments
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_twitter_impressions . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_twitter_total_engagement . "</td>";}
                $total_views += (int) $part_twitter_impressions;
                $total_engagements += (int) $part_twitter_total_engagement;
                
                
                if ($showColumnsArray['Tiktok_link']) {echo "<td class='editable-part' data-part-id='$part_id' data-field='part_tiktok_link'><a href='{$part_row['part_tiktok_link']}' target='_blank'>{$part_row['part_tiktok_link']}</a></td>";}
                
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_tiktok_views . "</td>";}
                if ($showColumnsArray['KPIs']) {echo "<td style = 'width: 50px;'>" . $part_tiktok_engagements . "</td>";}
                $total_views += (int) $part_tiktok_views;
                $total_engagements += (int) $part_tiktok_engagements;
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                //if ($showColumnsArray['KPIs']) {echo "<td></td>";}
                
                if ($showColumnsArray['Copies_number']) {echo "<td></td>";  }
                if ($showColumnsArray['Edit']) {echo "<td><a href='add_media_part.php?media_id=" . $media_id . "&part_id=" . $part_id . "'>Edit</a></td>";}
                if ($is_admin && $showColumnsArray['Delete']) {
                echo "<td><a href='delete_media_part.php?part_id=" . $part_id . "'>Delete</a></td>";
                }
            }
            echo "</td>";
            echo "</tr>";
      }
    }
}
echo "</tbody>";
echo "</table>";
echo "</div>"; 
echo "</div>"; 
$db = null;

echo '
<div style="display: flex; justify-content: space-between; font-family: monospace; padding-top:5px;">
    <div>
        Original: ' . $row_num . ' | Copies: ' . $copies_count . ' | Total: ' . ($copies_count + $row_num) . '
        | KPIS | Total views: ' . $total_views . ' | Total engagements: ' . $total_engagements . '
    </div>
    <div>Version: ' . $version . '</div>
</div>';



?>





<!-- Dark Overlay Background -->
<div id="authorOverlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:999;" onclick="closeModal()"></div>

<!-- Popup Modal -->
<div id="authorModal" style="display: none; position: fixed; top: 20%; left: 50%; transform: translate(-50%, 0); background: white; padding: 20px; border: 1px solid #ccc; z-index: 1000;">
    <h3>Select Authors</h3>
    <form id="authorForm">
        <div id="authorList"></div> <!-- List of checkboxes -->
        <input type="text" id="otherAuthor" placeholder="Other (write here)">
        <button type="button" onclick="saveAuthors()">Save</button>
        <button type="button" onclick="closeModal()">Cancel</button>
    </form>
</div>

<script>
function editAuthors(mediaId) {
    // Show the modal and overlay
    document.getElementById('authorModal').style.display = 'block';
    document.getElementById('authorOverlay').style.display = 'block';

    // Fetch available authors & pre-check selected ones
    fetch('fetch_authors.php?media_id=' + mediaId)
    .then(response => response.text())
    .then(data => {
        document.getElementById('authorList').innerHTML = data;
        document.getElementById('authorModal').dataset.mediaId = mediaId;
    });
}

function closeModal() {
    // Hide modal and overlay
    document.getElementById('authorModal').style.display = 'none';
    document.getElementById('authorOverlay').style.display = 'none';
}

function saveAuthors() {
    let mediaId = document.getElementById('authorModal').dataset.mediaId;
    let selectedAuthors = [];

    // Get checked authors
    document.querySelectorAll('input[name="author"]:checked').forEach((checkbox) => {
        selectedAuthors.push(checkbox.value);
    });

    // Include "Other" author if filled
    let otherAuthor = document.getElementById('otherAuthor').value.trim();
    if (otherAuthor) {
        selectedAuthors.push(otherAuthor);
    }

    // Send data via AJAX
    fetch('save_authors.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_id: mediaId, authors: selectedAuthors })
    })
    .then(response => response.text())
    .then(message => {
        //alert(message);  // Show response message
        closeModal();    // Close modal
        location.reload(); // Refresh page to reflect changes
    });
}
</script>










</body>

<script> // saving vertical and horizontal scroll position
    window.addEventListener('load', function() {
        var table = document.getElementById('table1');
        table.scrollTop = localStorage.getItem('scrollPositionTop');
        table.scrollLeft = localStorage.getItem('scrollPositionLeft');
    });
    window.addEventListener('beforeunload', function() {
        var table = document.getElementById('table1');
        localStorage.setItem('scrollPositionTop', table.scrollTop);
        localStorage.setItem('scrollPositionLeft', table.scrollLeft);
    });
</script>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script> //allow editing fields by double click
$(document).ready(function() {
  $('.editable').on('dblclick', function() {
    var cell = $(this);
    var mediaId = cell.data('media-id');
    var field = cell.data('field');
    var originalValue = cell.text();
    var input = $('<input type="text" value="' + originalValue + '">');
    input.on('blur keydown', function(e) {
      if (e.type === 'keydown' && e.keyCode !== 13) {
        return;
      }
      var newValue = input.val();
      $.post('edit_media_field.php', { media_id: mediaId, field: field, value: newValue }, function(response) {
        if (field === 'title_english' || field === 'title') {
          cell.text(newValue);
        } else {
          cell.html('<a href="' + newValue + '" target="_blank">' + newValue + '</a>');
        }
        if (field === 'media_youtube_link') {
          location.reload();
        }
      });
      input.remove();
    });
    cell.html(input);
    input.focus();
  });
});
//make the parts editable as well
$(document).ready(function() {
  $('.editable-part').on('dblclick', function() {
    var cell = $(this);
    var partId = cell.data('part-id');
    var field = cell.data('field');
    var originalValue = cell.text();
    var input = $('<input type="text" value="' + originalValue + '">');
    input.on('blur keydown', function(e) {
      if (e.type === 'keydown' && e.keyCode !== 13) {
        return;
      }
      var newValue = input.val();
      $.post('edit_media_part_field.php', { part_id: partId, field: field, value: newValue }, function(response) {
        
        if (field === 'part_title') {
          cell.text(newValue);
        } else {
          cell.html('<a href="' + newValue + '" target="_blank">' + newValue + '</a>');
        }
      });
      input.remove();
    });
    cell.html(input);
    input.focus();
  });
});

function updateWhatsappStatus(checkbox, id, type) { //update whatsapp
  var isChecked = checkbox.checked ? 1 : 0;
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "update_whatsapp_status.php", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.send("id=" + id + "&whatsapp_status=" + isChecked + "&type=" + type);
}
</script>


<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {
    $('.collapse-button').on('click', function() {
        var mediaId = $(this).data('media-id');

        $.post('add_media_part_ajax.php', { media_id: mediaId }, function(response) {
              location.reload();   
        });
    });
});
</script>


<script>
// Function to handle the status click
function handleStatusClick(event, mediaId, greenButtonStatus) {
    if (greenButtonStatus !== 'filled') {
        event.preventDefault(); // Prevent the default action
        alert('You can only set the status to "reviewed" if the status is already "filled".');
        return false;
    }

    // Call updateStatus if the status is valid
    updateStatus(mediaId, 'reviewed');
}

// Function to update the status in the database
function updateStatus(mediaId, status) {
    fetch('update_status.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mediaId: mediaId, status: status }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Status updated successfully!');
        } else {
            alert('Failed to update status.');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
</script>
















<!-- Datalist for media sources -->
<datalist id="sourceList">
  <?php
  $sources = file('media_sources.csv', FILE_IGNORE_NEW_LINES);
  foreach ($sources as $source) {
    echo "<option value=\"$source\">";
  }
  ?>
</datalist>

<!-- Popup for editing media source -->
<div id="mediaPopup" style="display:none; position:fixed; top:30%; left:50%; transform:translate(-50%, -50%); background:#fff; padding:20px; border:1px solid #ccc; z-index:1000;">
  <h3>Edit Media Source</h3>
  <input type="hidden" id="popupMediaId">
  <input type="text" id="popupSourceInput" list="sourceList" style="width:100%; margin-bottom:10px;">
  <button onclick="saveMediaSource()">Save</button>
  <button onclick="closePopup()">Cancel</button>
</div>

<!-- Overlay background -->
<div id="popupOverlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:999;" onclick="closePopup()"></div>

<script>
function openPopup(id, currentSource) {
    document.getElementById('popupMediaId').value = id; 
    document.getElementById('popupSourceInput').value = currentSource;
    document.getElementById('mediaPopup').style.display = 'block';
    document.getElementById('popupOverlay').style.display = 'block';
}

function closePopup() {
    document.getElementById('mediaPopup').style.display = 'none';
    document.getElementById('popupOverlay').style.display = 'none';
}

function saveMediaSource() {
    const id = document.getElementById('popupMediaId').value;
    const newSource = document.getElementById('popupSourceInput').value;

    fetch('update_media_source.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, media_source: newSource }) 
    })
    .then(response => response.json())
    .then(result => {
        if (result.message) {
            location.reload(); // Refresh to see updated data
        } else {
            alert('Update failed: ' + JSON.stringify(result));
        }
    });
}


</script>
