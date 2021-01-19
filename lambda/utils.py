import logging
import os
import boto3
from botocore.exceptions import ClientError

def play(url, offset, text, card_data, response_builder):
    """Function to play audio.
    Using the function to begin playing audio when:
        - Play Audio Intent is invoked.
        - Resuming audio when stopped / paused.
        - Next / Previous commands issues.
    https://developer.amazon.com/docs/custom-skills/audioplayer-interface-reference.html#play
    REPLACE_ALL: Immediately begin playback of the specified stream,
    and replace current and enqueued streams.
    """
    # type: (str, int, str, Dict, ResponseFactory) -> Response
    if card_data:
        response_builder.set_card(
            StandardCard(
                title=card_data["title"], text=card_data["text"],
                image=Image(
                    small_image_url=card_data["small_image_url"],
                    large_image_url=card_data["large_image_url"])
            )
        )

    # Using URL as token as they are all unique
    response_builder.add_directive(
        PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    token=url,
                    url=url,
                    offset_in_milliseconds=offset,
                    expected_previous_token=None),
                metadata=add_screen_background(card_data) if card_data else None
            )
        )
    ).set_should_end_session(True)

    if text:
        response_builder.speak(text)

    return response_builder.response

def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object with a capped expiration of 60 seconds

    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
    try:
        bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=60*1)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response