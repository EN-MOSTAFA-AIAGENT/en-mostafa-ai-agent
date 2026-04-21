<?php
if ( ! defined( 'ABSPATH' ) ) exit;
class AIWA_Elementor { private static $i=null; public static function get_instance(){if(!self::$i)self::$i=new self();return self::$i;} }
class AIWA_LearnDash { private static $i=null; public static function get_instance(){if(!self::$i)self::$i=new self();return self::$i;} }
class AIWA_WPCLI     { private static $i=null; public static function get_instance(){if(!self::$i)self::$i=new self();return self::$i;} }
